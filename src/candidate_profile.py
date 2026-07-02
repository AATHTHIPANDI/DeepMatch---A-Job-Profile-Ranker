import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL
from src.models import CandidateProfile, WorkExperience, PlatformActivity

logger = logging.getLogger(__name__)

def parse_date_to_year_fraction(date_str: str) -> datetime:
    """Helper to parse a date string into a datetime object for tenure calculation."""
    date_str = date_str.strip().lower()
    if not date_str or date_str in ["present", "current", "now"]:
        # Mock date reference from user metadata: 2026-07-02
        return datetime(2026, 7, 2)
        
    formats = [
        "%b %Y", "%B %Y", "%m/%Y", "%Y-%m-%d", "%Y-%m", "%Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    # Fallback to year extraction
    try:
        # Check if year is in the string (4 consecutive digits)
        import re
        match = re.search(r"\b(19|20)\d{2}\b", date_str)
        if match:
            year = int(match.group(0))
            return datetime(year, 1, 1)
    except Exception:
        pass
        
    return datetime(2020, 1, 1) # generic fallback

def calculate_tenure_years(start_str: str, end_str: str) -> float:
    """Calculates tenure in years between two date strings."""
    start_dt = parse_date_to_year_fraction(start_str)
    end_dt = parse_date_to_year_fraction(end_str)
    
    delta = end_dt - start_dt
    years = delta.days / 365.25
    return max(round(years, 2), 0.1)

def synthesize_candidate_profile(raw_data: Dict[str, Any]) -> CandidateProfile:
    """
    Synthesizes career history, programmatic tenure calculations, skills overlap, 
    and LLM qualitative analysis to populate a CandidateProfile.
    """
    candidate_id = raw_data.get("candidate_id", "unknown")
    name = raw_data.get("name", "Unknown Candidate")
    contact = raw_data.get("contact", {})
    summary = raw_data.get("summary", "")
    explicit_skills = raw_data.get("skills", [])
    
    # Calculate programmatics for each job
    raw_exp = raw_data.get("experience", [])
    processed_exp = []
    overall_tenure = 0.0
    
    for job in raw_exp:
        start_date = job.get("start_date", "2020-01")
        end_date = job.get("end_date", "Present")
        tenure = calculate_tenure_years(start_date, end_date)
        overall_tenure += tenure
        
        processed_exp.append({
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "start_date": start_date,
            "end_date": end_date,
            "tenure_years": tenure,
            "description": job.get("description", "")
        })
        
    avg_tenure = overall_tenure / len(processed_exp) if processed_exp else 0.0
    
    # Optional Platform Activity
    raw_platform = raw_data.get("platform_activity", {})
    platform_activity = None
    if raw_platform:
        platform_activity = PlatformActivity(
            github_commits_past_year=raw_platform.get("github_commits_past_year"),
            github_repo_relevance=raw_platform.get("github_repo_relevance"),
            linkedin_activity_recency=raw_platform.get("linkedin_activity_recency"),
            stackoverflow_reputation=raw_platform.get("stackoverflow_reputation")
        )
        
    # Query Groq to extract qualitative carrier metrics
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")
        
    client = Groq(api_key=GROQ_API_KEY)
    
    # Structure payload for LLM analysis
    jobs_summary_text = ""
    for idx, j in enumerate(processed_exp):
        jobs_summary_text += (
            f"Job #{idx+1}: {j['title']} at {j['company']} ({j['tenure_years']} years)\n"
            f"Description: {j['description']}\n\n"
        )
        
    system_prompt = (
        "You are an expert recruiter and career strategist. Your job is to analyze a candidate's profile "
        "and perform deep analysis on career progression, ownership scope, achievement indicators, and "
        "inferred skills. Ground your analysis strictly in their provided description, do not hallucinate metrics.\n"
        "You must respond with a JSON object containing the following keys:\n"
        "{\n"
        '  "inferred_skills": ["List of all skills inferred from descriptions across all jobs that were NOT explicitly listed"],\n'
        '  "jobs": [\n'
        "    {\n"
        '      "inferred_skills": ["Skills specific to this job description"],\n'
        '      "growth_signals": ["Specific signs of growth (promotions, expanding tech ownership, scale shifts)"],\n'
        '      "scope_of_ownership": "Short summary of technical/operational scope owned (systems, databases, team size)",\n'
        '      "achievement_language": "Action verbs or quantifiable achievements extracted (e.g. optimized performance, reduced latency)",\n'
        '      "is_relevant_to_tech_roles": true/false\n'
        "    }\n"
        "  ],\n"
        '  "behavioral_summary": "Overall synthesis of their ownership scope, achievement style, work stability, and communication signals.",\n'
        '  "growth_trajectory": "One of: rapid growth, steady promotion, lateral progression, declining responsibility, job-hopping"\n'
        "}\n"
        "The length of the 'jobs' array MUST match the number of jobs sent in the raw data."
    )
    
    user_prompt = (
        f"Candidate Summary: {summary}\n"
        f"Explicit Skills: {explicit_skills}\n"
        f"Work Experience Details:\n{jobs_summary_text}"
    )
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        inferred_skills = list(set([s.strip() for s in analysis.get("inferred_skills", [])]))
        llm_jobs = analysis.get("jobs", [])
        
        # Merge LLM analysis back into jobs
        final_experiences = []
        for i, pe in enumerate(processed_exp):
            # Default values if index mismatches
            lj = llm_jobs[i] if i < len(llm_jobs) else {}
            
            final_experiences.append(WorkExperience(
                title=pe["title"],
                company=pe["company"],
                start_date=pe["start_date"],
                end_date=pe["end_date"],
                tenure_years=pe["tenure_years"],
                description=pe["description"],
                inferred_skills=lj.get("inferred_skills", []),
                growth_signals=lj.get("growth_signals", []),
                scope_of_ownership=lj.get("scope_of_ownership", ""),
                achievement_language=lj.get("achievement_language", ""),
                is_relevant=lj.get("is_relevant_to_tech_roles", True)
            ))
            
        all_skills = list(set([s.lower() for s in explicit_skills + inferred_skills]))
        
        return CandidateProfile(
            candidate_id=candidate_id,
            name=name,
            contact=contact,
            summary=summary,
            explicit_skills=explicit_skills,
            inferred_skills=inferred_skills,
            experience=final_experiences,
            behavioral_summary=analysis.get("behavioral_summary", ""),
            overall_tenure_years=round(overall_tenure, 2),
            avg_tenure_years=round(avg_tenure, 2),
            growth_trajectory=analysis.get("growth_trajectory", "stable"),
            platform_activity=platform_activity
        )
        
    except Exception as e:
        logger.error(f"Error synthesizing candidate profile: {e}")
        # Fallback profile
        fallback_experiences = [
            WorkExperience(
                title=pe["title"],
                company=pe["company"],
                start_date=pe["start_date"],
                end_date=pe["end_date"],
                tenure_years=pe["tenure_years"],
                description=pe["description"],
                inferred_skills=[],
                growth_signals=[],
                scope_of_ownership="General ownership",
                achievement_language="Accomplished general engineering duties",
                is_relevant=True
            ) for pe in processed_exp
        ]
        return CandidateProfile(
            candidate_id=candidate_id,
            name=name,
            contact=contact,
            summary=summary,
            explicit_skills=explicit_skills,
            inferred_skills=[],
            experience=fallback_experiences,
            behavioral_summary="Fallback parsed profile due to synthesis error.",
            overall_tenure_years=round(overall_tenure, 2),
            avg_tenure_years=round(avg_tenure, 2),
            growth_trajectory="stable",
            platform_activity=platform_activity
        )

def parse_raw_resume_text(resume_text: str) -> Dict[str, Any]:
    """
    Parses unstructured raw resume text using Groq's LLM and extracts a structured dictionary
    that can be digested by synthesize_candidate_profile.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    client = Groq(api_key=GROQ_API_KEY)
    
    system_prompt = (
        "You are an expert recruitment parser. Your task is to analyze raw resume text and extract "
        "the key details into a structured JSON format. Be highly objective and ground all values "
        "strictly in the resume text.\n"
        "You must respond with a JSON object that matches the following schema:\n"
        "{\n"
        '  "name": "Full name of the candidate (if not found, use \'Unknown Candidate\')",\n'
        '  "contact": {\n'
        '    "email": "Email address (if not found, use empty string)",\n'
        '    "phone": "Phone number (if not found, use empty string)",\n'
        '    "location": "City, State or country (if not found, use empty string)"\n'
        '  },\n'
        '  "summary": "A brief 1-2 sentence profile summary or bio. If missing, summarize their main background.",\n'
        '  "skills": ["List of explicit technologies, frameworks, databases, or libraries listed in their skills section"],\n'
        '  "experience": [\n'
        '    {\n'
        '      "title": "Exact job title",\n'
        '      "company": "Company name",\n'
        '      "start_date": "Start date of employment (e.g., Jan 2021, 2021-01, or 2021)",\n'
        '      "end_date": "End date of employment (e.g., Dec 2022, or \'Present\')",\n'
        '      "description": "Responsibilities and accomplishments. Retain key numbers, actions, and projects."\n'
        '    }\n'
        '  ]\n'
        "}\n"
        "Make sure the dates match the format of the text. Keep descriptions faithful to the source."
    )
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the raw resume text:\n\n{resume_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        parsed_data = json.loads(response.choices[0].message.content)
        # Ensure a candidate_id is present
        import hashlib
        name = parsed_data.get("name", "candidate")
        cand_hash = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
        parsed_data["candidate_id"] = f"cand-{cand_hash}"
        return parsed_data
    except Exception as e:
        logger.error(f"Error parsing raw resume text: {e}")
        # Return a fallback empty structure
        return {
            "candidate_id": "cand-fallback",
            "name": "Unknown Candidate",
            "contact": {},
            "summary": "Could not parse candidate summary from text.",
            "skills": [],
            "experience": []
        }

# Simple standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_candidate = {
        "candidate_id": "cand-001",
        "name": "Jane Doe",
        "contact": {"email": "jane@example.com"},
        "summary": "Experienced Python Backend Engineer focused on performance and API design.",
        "skills": ["Python", "Flask", "PostgreSQL", "Docker"],
        "experience": [
            {
                "title": "Software Engineer II",
                "company": "PaymentCorp",
                "start_date": "Jan 2023",
                "end_date": "Present",
                "description": "Owned database migration from MySQL to PostgreSQL. Led design ofpayment callback API, improving latency by 200ms."
            },
            {
                "title": "Junior Developer",
                "company": "WebStartup",
                "start_date": "Jun 2021",
                "end_date": "Dec 2022",
                "description": "Wrote backend endpoints in Python/Flask. Implemented Docker containerization for local development environment."
            }
        ],
        "platform_activity": {
            "github_commits_past_year": 120,
            "github_repo_relevance": 0.85,
            "linkedin_activity_recency": "active",
            "stackoverflow_reputation": 450
        }
    }
    
    profile = synthesize_candidate_profile(sample_candidate)
    print("Synthesized Candidate Profile:")
    print(profile.model_dump_json(indent=2))
