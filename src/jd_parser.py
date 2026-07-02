import json
import logging
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL
from src.models import JobDescriptionIntent

logger = logging.getLogger(__name__)

def parse_job_description(jd_text: str) -> JobDescriptionIntent:
    """
    Parses a raw job description text using Groq's LLM and structures it
    into a JobDescriptionIntent object. Handles messy/unstructured inputs gracefully.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    client = Groq(api_key=GROQ_API_KEY)
    
    system_prompt = (
        "You are an expert technical recruiting coordinator. Your job is to analyze a raw job description (JD) "
        "and extract a structured representation of the hiring manager's intent. "
        "Focus on semantic understanding rather than raw keyword counting. "
        "For example, look for transferable skills, domain requirements, and implied soft skills. "
        "You must respond with a JSON object that matches the following structure:\n"
        "{\n"
        '  "role_title": "Clean, standard title of the role",\n'
        '  "seniority_level": "One of: Intern, Junior, Mid, Senior, Lead, Principal, Director/VP",\n'
        '  "domain": "One of: Backend, Frontend, Fullstack, Data, DevOps, Mobile, Security, QA, Product, Other",\n'
        '  "must_have_skills": ["List of non-negotiable core technical skills/platforms"],\n'
        '  "nice_to_have_skills": ["List of auxiliary/nice-to-have technologies, frameworks, or tools"],\n'
        '  "implied_soft_skills": ["Soft skills/behaviors implied by context, e.g. adaptability, high-growth pace"],\n'
        '  "min_years_experience": null or integer number of years requested,\n'
        '  "summary": "A concise paragraph summarizing the core mission and focus of this role."\n'
        "}\n"
        "Ensure all fields are filled. If years of experience are not specified, estimate or set to null."
    )
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the raw job description:\n\n{jd_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        raw_json_str = response.choices[0].message.content
        logger.debug(f"Raw JD parsing response: {raw_json_str}")
        
        parsed_data = json.loads(raw_json_str)
        
        # Validate and return JobDescriptionIntent
        return JobDescriptionIntent(**parsed_data)
        
    except Exception as e:
        logger.error(f"Error parsing job description: {e}")
        # Return fallback mock structure on failure to degrade gracefully
        return JobDescriptionIntent(
            role_title="Software Engineer",
            seniority_level="Mid",
            domain="Fullstack",
            must_have_skills=["software engineering"],
            nice_to_have_skills=[],
            implied_soft_skills=["collaboration"],
            min_years_experience=3,
            summary="A standard software engineering role extracted via fallback."
        )

# Simple standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_jd = """
    We are looking for a Senior Developer to join our fast-paced fintech startup.
    You will own the backend services responsible for payment processing.
    Must have extensive experience with Python, writing robust APIs (FastAPI preferred).
    Knowledge of Postgres is critical. You will work closely with frontend teams building with React.
    Ideal candidates have 5+ years of experience and are excited to own projects end-to-end.
    """
    intent = parse_job_description(sample_jd)
    print("Parsed JD Intent:")
    print(intent.model_dump_json(indent=2))
