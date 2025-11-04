from venv import logger

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

# Import custom modules
from markdown_utils import generate_pdf_from_json, generate_pdf_from_markdown
from resume_tailor import tailor_resume, convert_json_to_text, convert_json_to_markdown
from job_analysis import generate_cover_letter, generate_question_answers

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()

# Configure Google Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Create output directory for intermediate files
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Resumer API",
    description="API for customizing resumes based on job descriptions using AI",
    version="1.0.0"
)

# Configure CORS
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production":
    allowed_origins = [
        "https://easyhired.online",
        "https://www.easyhired.online"
    ]
else:
    allowed_origins = ["*"]  # Allow all origins in development

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

class Token(BaseModel):
    token: str
    user: User

class JobSubmission(BaseModel):
    job_description: str
    questions: Optional[List[str]] = None
    template: Optional[str] = None
    return_json: Optional[bool] = False

class TailoredResumeResponse(BaseModel):
    resume_url: str
    cover_letter_url: Optional[str] = None
    answers: Optional[List[str]] = None
    json_path: Optional[str] = None
    text_path: Optional[str] = None

# Authentication functions
def load_users():
    with open("users.json", "r") as f:
        return json.load(f)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(name: str, password: str):
    users = load_users()
    for user in users:
        if user["username"] == name and user["password"] == password:
            return user
    return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    users = load_users()
    user = None
    for u in users:
        if u["username"] == username:
            user = u
            break
    
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
async def read_root():
    return {"message": "Resumer API is running"}

@app.post("/signin", response_model=Token)
async def signin(user_login: UserLogin):
    user = authenticate_user(user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {
        "token": access_token, 
        "user": {"username": user["username"]}
    }

@app.post("/tailor-resume", response_model=TailoredResumeResponse)
async def tailor_resume_endpoint(job_data: JobSubmission, current_user: dict = Depends(get_current_user)):
    """Generate a tailored resume based on the job description."""
    try:
        # Tailor the resume based on the job description
        template_file = f"resume_templates/{job_data.template}"
        json_path, tailored_resume = tailor_resume(job_data.job_description, model, template_file)

        # Convert JSON to text format
        text_path, _ = convert_json_to_text(tailored_resume)
        # Extract template name from the file path for the output filename
        template_name = os.path.splitext(os.path.basename(job_data.template))[0] if job_data.template else "default"
        
        # Generate PDF from the tailored resume
        output_dir = Path("output")
        pdf_path = output_dir / f"{template_name}_resume.pdf"

        # Generate the PDF
        generate_pdf_from_json(tailored_resume, pdf_path)

        # Create a response with appropriate paths
        response = {
            "resume_url": f"/download/resume/{pdf_path.name}",
        }

        # Generate cover letter if requested
        cover_letter_path = None
        if tailored_resume:
            cover_letter_path = generate_cover_letter(tailored_resume, job_data.job_description, model, template_name)
            if cover_letter_path:
                response["cover_letter_url"] = f"/download/cover_letter/{cover_letter_path.name}"
        # Generate answers to questions if provided
        answers = None
        if job_data.questions and len(job_data.questions) > 0:
            answers = generate_question_answers(job_data.questions, job_data.job_description, tailored_resume, model)
            response["answers"] = answers
        
        # Include JSON and text paths if requested
        if job_data.return_json:
            response["json_path"] = str(json_path)
            response["text_path"] = str(text_path)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tailoring resume: {str(e)}")

@app.get("/download/resume/{filename}")
async def download_resume(filename: str, mode: Optional[str] = None):
    """Download a generated resume."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Extract template name from the filename
    template_name = file_path.name.split("_resume")[0] if "_resume" in file_path.name else "tailored"
    
    if mode == "download":
        return FileResponse(
            path=file_path,
            filename=f"{template_name}_resume.pdf",
            media_type="application/pdf"
        )
    else:
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"}
        )
    
@app.get("/download/cover_letter/{filename}")
async def download_cover_letter(filename: str, mode: Optional[str] = None):
    """Download a generated cover letter."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Cover letter not found")
    
    # Extract template name from the filename
    template_name = file_path.name.split("_cover_letter")[0] if "_cover_letter" in file_path.name else "default"
    
    if mode == "download":
        return FileResponse(
            path=file_path,
            filename=f"{template_name}_cover_letter.pdf",
            media_type="application/pdf"
        )
    else:
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"}
        )

@app.get("/templates")
async def get_templates(current_user: dict = Depends(get_current_user)):
    """Get a list of available templates."""
    templates = os.listdir("resume_templates")
    return templates

@app.get("/cover_letter/content/{filename}")
async def get_cover_letter_content(filename: str, current_user: dict = Depends(get_current_user)):
    """Get the markdown content of a cover letter."""
    # Convert PDF filename to MD filename
    md_filename = filename.replace(".pdf", ".md")
    file_path = OUTPUT_DIR / md_filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Cover letter markdown not found")
    
    try:
        with open(file_path, "r") as f:
            content = f.read()
        
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading cover letter content: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
