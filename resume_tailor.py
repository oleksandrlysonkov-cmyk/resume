import json
from datetime import datetime
from pathlib import Path
import os
import re

def tailor_resume(job_description, model, template = "resume_templates/michael.json"):
    """
    Tailor the resume based on the job description
    Uses the template resume JSON and creates a tailored version
    """
    # Load the template resume
    template_path = os.path.join(os.path.dirname(__file__), template)
    with open(template_path, "r") as f:
        resume_structure = json.load(f)
    
    # Create the tailoring prompt
    tailoring_prompt = f"""
    I need to tailor my resume for a specific job. I'll provide my current resume structure in JSON format and the job description.
    
    JOB DESCRIPTION:
    {job_description}
    
    MY CURRENT RESUME (in JSON format):
    {json.dumps(resume_structure, indent=2)}
    
    Based on the job description, please create a tailored version of my resume by modifying the following sections:
    
    1. Summary: Rewrite to emphasize skills and experiences relevant to this specific job
       - Use <strong>bold</strong> formatting for technical skills (e.g. <strong>JavaScript</strong>, <strong>Python</strong>, <strong>AWS</strong>, etc)
       - Make the summary concise and focused on the job requirements
    
    2. Experience: For each experience entry:
       - Keep the company name and period the same
       - Adjust the job title to match the job description
       - Tailor the summary to match the job description, to highlight relevant achievements, using markdown for technical terms
       - The 'highlights' section is optional
       - If you include highlights, use markdown to bold important technical terms
       - re-write and tailor each highlight to better match the job requirements
       - Adjust the skills to better match the job requirements (add or remove skills as needed)
    
    3. Skills: Reorganize and emphasize skills relevant to the job
       - Prioritize skills mentioned in the job description
       - Filter out unrelevant skills
       - Keep the same structure but adjust the content
    
    Do NOT modify:
    - Name and contact information
    - Company names and dates
    - Education section structure
    
    Important: Use <strong>bold</strong> syntax directly in your text for all technical terms and skills (like <strong>JavaScript</strong>, <strong>Python</strong>, <strong>AWS</strong>, etc). And convert all markdown syntax(**bold**) to <strong>bold</strong> format. And NEVER use junior for any title.
    
    Return ONLY a JSON object with the same structure as the input but with tailored content. 
    Do not include any explanations or additional text outside the JSON.
    """
    
    response = model.generate_content(tailoring_prompt)
    
    try:
        # Attempt to parse the response as JSON
        # Extract JSON if it's wrapped in markdown code blocks
        text = response.text
        if '```json' in text and '```' in text.split('```json', 1)[1]:
            json_str = text.split('```json', 1)[1].split('```', 1)[0].strip()
        elif '```' in text and '```' in text.split('```', 1)[1]:
            json_str = text.split('```', 1)[1].split('```', 1)[0].strip()
        else:
            json_str = text
            
        tailored_resume = json.loads(json_str)
        
        # Save the tailored resume to a file
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file_path = output_dir / f"tailored_resume_{timestamp}.json"
        
        with open(json_file_path, "w") as f:
            json.dump(tailored_resume, f, indent=2)
            
        return json_file_path, tailored_resume
    
    except json.JSONDecodeError:
        # If JSON parsing fails, save the raw text
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_file_path = output_dir / f"tailored_resume_raw_{timestamp}.txt"
        
        with open(raw_file_path, "w") as f:
            f.write(response.text)
            
        raise Exception(f"Failed to parse tailored resume as JSON. Raw output saved to {raw_file_path}")

def convert_json_to_text(tailored_resume_json):
    """
    Convert the tailored resume JSON to a formatted text
    This can be used for later PDF generation
    """
    # Convert the resume JSON to formatted text
    if isinstance(tailored_resume_json, str):
        # If path is provided, load the JSON
        with open(tailored_resume_json, "r") as f:
            tailored_resume = json.load(f)
    else:
        # If the JSON object is provided directly
        tailored_resume = tailored_resume_json
    
    # Convert to text format
    text_content = []
    
    # Add name and contact information
    text_content.append(tailored_resume["name"])
    
    # Add contact information as separate lines
    contact = tailored_resume["contact"]
    for key, value in contact.items():
        text_content.append(f"{key}: {value}")
    
    # Add separator
    text_content.append("----")
    
    # Add summary
    text_content.append("SUMMARY")
    text_content.append(tailored_resume["summary"])
    text_content.append("")
    
    # Add references if they exist
    if "references" in tailored_resume and tailored_resume["references"]:
        text_content.append("PROFESSIONAL REFERENCES")
        for ref in tailored_resume["references"]:
            text_content.append(f"{ref.get('name', '')} - Link: {ref.get('link', '')}")
        text_content.append("")
    
    # Add experience
    text_content.append("EXPERIENCE")
    
    for exp in tailored_resume["experience"]:
        # Title and company
        title_company = f"{exp.get('title', '')} at {exp.get('company', '')}"
        text_content.append(title_company)
        
        # Period
        if "period" in exp:
            text_content.append(exp["period"])
        
        # Skills used
        if "skills" in exp and exp["skills"]:
            if isinstance(exp["skills"], list):
                text_content.append("Skills: " + ", ".join(exp["skills"]))
            else:
                text_content.append(f"Skills: {exp['skills']}")
        
        # Summary
        if "summary" in exp:
            text_content.append(exp["summary"])
        
        # Highlights/bullet points
        if "highlights" in exp and exp["highlights"]:
            for highlight in exp["highlights"]:
                text_content.append(f"• {highlight}")
        
        text_content.append("")
    
    # Add skills section
    text_content.append("SKILLS")
    
    skills = tailored_resume["skills"]
    if isinstance(skills, dict):
        for category, skill_list in skills.items():
            if isinstance(skill_list, list):
                text_content.append(f"{category}: {', '.join(skill_list)}")
            else:
                text_content.append(f"{category}: {skill_list}")
    elif isinstance(skills, list):
        text_content.append(", ".join(skills))
    else:
        text_content.append(skills)
    
    text_content.append("")
    
    # Add education
    text_content.append("EDUCATION")
    
    education = tailored_resume["education"]
    if isinstance(education, dict):
        text_content.append(f"{education.get('degree', '')} - {education.get('university', '')}")
        if "period" in education:
            text_content.append(education["period"])
        if "description" in education:
            text_content.append(education["description"])
    elif isinstance(education, list):
        for edu in education:
            if isinstance(edu, dict):
                text_content.append(f"{edu.get('degree', '')} - {edu.get('university', '')}")
                if "period" in edu:
                    text_content.append(edu["period"])
                if "description" in edu:
                    text_content.append(edu["description"])
            else:
                text_content.append(edu)
    else:
        text_content.append(education)
    
    # Combine all text
    full_text = "\n".join(text_content)
    
    # Save the text version
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_file_path = output_dir / f"tailored_resume_text_{timestamp}.txt"
    
    with open(text_file_path, "w") as f:
        f.write(full_text)
    
    return text_file_path, full_text

def convert_json_to_markdown(tailored_resume_json):
    """
    Convert the tailored resume JSON to a well-formatted markdown
    This is used for PDF generation with styling
    Uses the template files in the output_template directory
    """
    # Load the JSON if a path is provided
    if isinstance(tailored_resume_json, str):
        with open(tailored_resume_json, "r") as f:
            tailored_resume = json.load(f)
    else:
        tailored_resume = tailored_resume_json
    
    # Load the main template file
    template_dir = os.path.join(os.path.dirname(__file__), "output_template")
    template_path = os.path.join(os.path.dirname(__file__), "output_template.md")
    try:
        with open(template_path, "r") as f:
            template_content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Resume template markdown file not found at {template_path}")
    
    # Load all section templates
    def load_template(filename):
        file_path = os.path.join(template_dir, filename)
        with open(file_path, "r") as f:
            return f.read()
    
    top_section_template = load_template("top_section.md")
    summary_section_template = load_template("summary_section.md")
    references_section_template = load_template("references_section.md")
    reference_item_template = load_template("reference_item.md")
    experiences_section_template = load_template("experiences_section.md")
    experience_item_template = load_template("experience_item.md")
    experience_highlights_template = load_template("experience_highlights.md")
    experience_highlight_item_template = load_template("experience_highlight_item.md")
    skills_section_template = load_template("skills_section.md")
    skill_section_item_template = load_template("skill_section_item.md")
    education_section_template = load_template("education_section.md")
    
    # Generate Top Section
    contact = tailored_resume["contact"]
    name = tailored_resume["name"]
    
    # Generate contact links HTML
    contact_links = []
    for key, value in contact.items():
        if key != "location":  # Skip location as it's displayed separately
            contact_links.append(f'<a href="{value}" style="margin: 0 0.5em; color: #0366d6; text-decoration: underline;">{key}</a>')
    
    contacts_html = " | ".join(contact_links)
    
    top_section = top_section_template
    top_section = top_section.replace("{{name}}", name)
    
    # Load and include location section only if it exists in contact
    location_section_template = load_template("location_section.md")
    location_section = ""
    if "location" in contact and contact["location"]:
        location = contact["location"]
        location_section = location_section_template.replace("{{location}}", location)
    
    top_section = top_section.replace("{{location_section}}", location_section)
    top_section = top_section.replace("{{contacts}}", contacts_html)
    
    # Generate Summary Section
    summary = tailored_resume["summary"]
    summary_section = summary_section_template.replace("{{summary}}", summary)
    
    # Generate Experiences Section
    experiences = ""
    for exp in tailored_resume["experience"]:
        # Extract information
        title = exp.get('title', '')
        company = exp.get('company', '')
        
        # Parse location from company string if it's in parentheses
        location = ""
        if "(" in company and ")" in company:
            company_parts = company.split("(", 1)
            company = company_parts[0].strip()
            location = company_parts[1].replace(")", "").strip()
        
        # Extract period and split into from/to
        period = exp.get('period', '')
        from_date = period
        to_date = ""
        if "-" in period:
            date_parts = period.split("-", 1)
            from_date = date_parts[0].strip()
            to_date = date_parts[1].strip()
        
        # Get summary and skills
        description = exp.get('summary', '')
        skills_text = ""
        if "skills" in exp and exp["skills"]:
            if isinstance(exp["skills"], list):
                skills_text = ", ".join(exp["skills"])
            else:
                skills_text = str(exp["skills"])
        
        # Generate highlights section if needed
        highlights_html = ""
        highlights = exp.get('highlights', [])
        if highlights and any(h.strip() for h in highlights):
            highlight_items = ""
            for highlight in highlights:
                if highlight and highlight.strip():
                    highlight_item = experience_highlight_item_template.replace("{{highlight}}", highlight)
                    highlight_items += highlight_item
            
            highlights_html = experience_highlights_template.replace("{{highlights}}", highlight_items)
        
        # Create experience item by replacing placeholders
        experience_item = experience_item_template
        experience_item = experience_item.replace("{{position}}", title)
        experience_item = experience_item.replace("{{company_name}}", company)
        experience_item = experience_item.replace("{{location}}", location)
        experience_item = experience_item.replace("{{from}}", from_date)
        experience_item = experience_item.replace("{{to}}", to_date)
        experience_item = experience_item.replace("{{description}}", description)
        experience_item = experience_item.replace("{{skills}}", skills_text)
        experience_item = experience_item.replace("{{highlights}}", highlights_html)
        
        experiences += experience_item + "\n"
    
    # Combine experiences into the experiences section
    experiences_section = experiences_section_template.replace("{{experiences}}", experiences)
    
    # Generate Skills Section
    skills = tailored_resume["skills"]
    skills_html = ""
    if isinstance(skills, dict):
        for category, skill_list in skills.items():
            if isinstance(skill_list, list):
                skills_text = ", ".join(skill_list)
            else:
                skills_text = str(skill_list)
            
            skill_item = skill_section_item_template
            skill_item = skill_item.replace("{{category}}", category)
            skill_item = skill_item.replace("{{skills}}", skills_text)
            skills_html += skill_item + "\n"
    
    skills_section = skills_section_template.replace("{{skills}}", skills_html)
    
    # Generate Education Section
    # For now, using the template directly since it has fixed values
    # In a future enhancement, we could make this dynamic too
    education_section = education_section_template
    if isinstance(tailored_resume["education"], dict):
        education = tailored_resume["education"]
        degree = education.get("degree", "Bachelor of Information Technology")
        university = education.get("university", "James Cook University, Singapore")
        period = education.get("period", "Jan 2009 - Dec 2011")
        description = education.get("description", "Major concentration in Software Development, Algorithm Design, and Database Management Systems with distinction.")
        
        # Replace education information if different from defaults
        education_section = education_section.replace("{{degree}}", degree)
        education_section = education_section.replace("{{university}}", university)
        education_section = education_section.replace("{{period}}", period)
        education_section = education_section.replace("{{description}}", description)
    
    # Generate References Section (only if references exist and not empty)
    references_section = ""
    if "references" in tailored_resume and tailored_resume["references"]:
        references_html = ""
        for ref in tailored_resume["references"]:
            ref_item = reference_item_template
            ref_item = ref_item.replace("{{name}}", ref.get("name", ""))
            ref_item = ref_item.replace("{{text}}", ref.get("text", ""))
            ref_item = ref_item.replace("{{link}}", ref.get("link", "#"))
            references_html += ref_item
        
        references_section = references_section_template.replace("{{references}}", references_html)
    
    # Combine all sections into the main template
    template_content = template_content.replace("{{top_section}}", top_section)
    template_content = template_content.replace("{{summary_section}}", summary_section)
    template_content = template_content.replace("{{references_section}}", references_section)
    template_content = template_content.replace("{{experiences_section}}", experiences_section)
    template_content = template_content.replace("{{skills_section}}", skills_section)
    template_content = template_content.replace("{{education_section}}", education_section)
    
    # Save the markdown version
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file_path = output_dir / f"tailored_resume_markdown_{timestamp}.md"
    
    with open(markdown_file_path, "w") as f:
        f.write(template_content)
    
    return template_content