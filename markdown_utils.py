import json
from datetime import datetime
from pathlib import Path
import os
from markdown_pdf import MarkdownPdf, Section
import re
from resume_tailor import convert_json_to_markdown

def generate_pdf_from_markdown(markdown_content, output_path=None):
    """
    Generate a PDF from markdown content
    
    Args:
        markdown_content: Markdown text to convert to PDF
        output_path: Path to save the PDF (if None, generates in output directory)
    
    Returns:
        Path to the generated PDF
    """
    # Generate output path if not provided
    if output_path is None:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"document_{timestamp}.pdf"
    
    # Create a temporary markdown file
    markdown_path = Path(str(output_path).replace('.pdf', '.md'))
    with open(markdown_path, 'w') as f:
        f.write(markdown_content)
    
    try:
        # Define CSS for styling
        css = """
        @page {
            margin: 1in 1in 1in 1in;
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            line-height: 1.6;
            color: #333333;
            font-size: 11pt;
        }

        a {
            color: #0066cc;
            text-decoration: none;
        }

        h1, h2, h3, h4 {
            color: #222222;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }

        h1 {
            font-size: 20pt;
            text-align: center;
        }

        h2 {
            font-size: 16pt;
            border-bottom: 1px solid #cccccc;
            padding-bottom: 0.2em;
        }

        h3 {
            font-size: 14pt;
        }

        p {
            margin-top: 0.5em;
            margin-bottom: 0.5em;
        }

        ul {
            margin-top: 0.5em;
            margin-bottom: 0.5em;
        }

        li {
            margin-bottom: 0.3em;
        }

        blockquote {
            margin: 1em 0;
            padding-left: 1em;
            border-left: 4px solid #dddddd;
            color: #555555;
        }

        pre {
            background-color: #f5f5f5;
            padding: 0.5em;
            border-radius: 4px;
            overflow-x: auto;
        }

        code {
            font-family: 'Courier New', monospace;
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
        }
        """
        
        # Generate PDF from markdown
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(markdown_content, toc=False), user_css=css)
        pdf.meta["title"] = "Document"
        pdf.meta["author"] = "Resumer Application"

        pdf.save(output_path)
            
        return output_path
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise

def generate_pdf_from_json(tailored_resume_json, output_path=None):
    """
    Generate a PDF from a tailored resume JSON using markdown
    
    Args:
        tailored_resume_json: Path to JSON file or JSON object
        output_path: Path to save the PDF (if None, generates in output directory)
    
    Returns:
        Path to the generated PDF
    """
    # Load the JSON if a path is provided
    if isinstance(tailored_resume_json, str):
        with open(tailored_resume_json, 'r') as f:
            resume_data = json.load(f)
    else:
        resume_data = tailored_resume_json
    
    # Convert JSON to markdown format
    markdown_content = convert_json_to_markdown(resume_data)
    
    # Generate output path if not provided
    if output_path is None:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"tailored_resume_{timestamp}.pdf"
    
    # Create a temporary markdown file
    markdown_path = Path(str(output_path).replace('.pdf', '.md'))
    with open(markdown_path, 'w') as f:
        f.write(markdown_content)
    
    # Convert markdown to PDF
    try:
        # Define CSS for styling
        css = """
        :root {
            --primary-color: #0A3662;
            --secondary-color: #0366d6;
            --text-color: #333333;
            --light-gray: #666666;
            --border-color: #dddddd;
        }

        @page {
            margin: 0.75in 0.75in 0.5in 0.75in;
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            line-height: 1.5;
            color: var(--text-color);
            font-size: 10pt;
        }

        /* Center text alignment */
        .text-center {
            text-align: center;
        }

        /* Header styling */
        h1 {
            font-size: 2.5em;
            color: var(--primary-color);
            margin-bottom: 0.5em;
            font-weight: bold;
            text-align: center;
        }

        h2 {
            font-size: 1.5em;
            color: var(--primary-color);
            border-bottom: 1.5px solid var(--primary-color);
            padding-bottom: 0.2em;
            margin: 1.5em 0 0.5em 0;
        }

        h3 {
            font-size: 1.2em;
            color: var(--primary-color);
            margin: 0.8em 0 0.3em 0;
        }

        /* Links */
        a {
            color: var(--secondary-color);
            text-decoration: none;
        }

        /* Text styling */
        p {
            margin: 0.5em 0;
        }

        em {
            font-style: italic;
            color: var(--light-gray);
        }

        strong {
            font-weight: bold;
        }

        /* Summary section */
        .summary {
            border-left: 3px solid var(--primary-color);
            padding-left: 1em;
            margin: 1em 0;
        }

        /* Experience section */
        .experience-entry {
            margin-bottom: 1.5em;
        }

        .job-title {
            color: var(--primary-color);
            margin-bottom: 0.5em;
        }

        .job-meta {
            color: var(--light-gray);
            margin: 0.2em 0;
        }

        .job-location {
            font-weight: 500;
        }

        /* List styling */
        ul {
            margin: 0.5em 0;
            padding-left: 1.5em;
        }

        li {
            margin-bottom: 0.3em;
        }

        /* Skills section */
        .skills-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1em;
            margin: 1em 0;
        }

        .skill-category {
            border: 1px solid var(--border-color);
            padding: 1em;
            border-radius: 4px;
        }

        /* Contact section */
        .contact-links {
            display: flex;
            justify-content: center;
            margin: 1em 0;
        }

        .contact-link {
            margin: 0 10px;
        }
        """
        
        # Extract name from resume data for PDF metadata
        print('resumedata =', resume_data)
        name = "Resume"
        author = "Unknown"
        if "name" in resume_data:
            name = f"Resume - {resume_data['name']}"
            author = resume_data['name']
        
        # Generate PDF from markdown
        pdf = MarkdownPdf(toc_level=3)
        pdf.add_section(Section(markdown_content, toc=False), user_css=css)
        pdf.meta["title"] = name
        pdf.meta["author"] = author

        pdf.save(output_path)

        # Keep the temporary markdown file for debugging
        # (You can uncomment the code below to delete it if needed)
        # if markdown_path.exists():
        #     os.remove(markdown_path)
            
        return output_path
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise