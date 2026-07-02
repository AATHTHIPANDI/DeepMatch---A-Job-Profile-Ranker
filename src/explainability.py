import json
import logging
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL
from src.models import JobDescriptionIntent, CandidateProfile, SubScores, CandidateRationale

logger = logging.getLogger(__name__)

def generate_candidate_rationale(
    jd: JobDescriptionIntent,
    candidate: CandidateProfile,
    sub_scores: SubScores,
    score_flags: list
) -> CandidateRationale:
    """
    Generates a concise, evidence-grounded rationale for a candidate's ranking.
    Avoids vague LLM filler and grounds all claims in candidate details.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=GROQ_API_KEY)
    
    # Construct structured details to inject into the prompt
    cand_details = {
        "name": candidate.name,
        "summary": candidate.summary,
        "explicit_skills": candidate.explicit_skills,
        "inferred_skills": candidate.inferred_skills,
        "overall_tenure_years": candidate.overall_tenure_years,
        "avg_tenure_years": candidate.avg_tenure_years,
        "growth_trajectory": candidate.growth_trajectory,
        "experience": [
            {
                "title": exp.title,
                "company": exp.company,
                "tenure_years": exp.tenure_years,
                "description": exp.description,
                "growth_signals": exp.growth_signals,
                "scope_of_ownership": exp.scope_of_ownership,
                "achievement_language": exp.achievement_language
            } for exp in candidate.experience
        ]
    }
    
    jd_details = {
        "role_title": jd.role_title,
        "seniority_level": jd.seniority_level,
        "domain": jd.domain,
        "must_have_skills": jd.must_have_skills,
        "nice_to_have_skills": jd.nice_to_have_skills,
        "min_years_experience": jd.min_years_experience
    }
    
    sub_scores_dict = sub_scores.model_dump()
    
    system_prompt = (
        "You are an elite executive recruiter. Your task is to write an objective, evidence-based "
        "shortlisting rationale for a candidate against a specific Job Description (JD).\n"
        "Crucial Rules:\n"
        "1. NEVER use vague corporate filler or generic praise (like 'fast learner', 'excellent communication skills', 'great fit').\n"
        "2. Ground every single claim in direct evidence from the candidate's actual profile data: quote metrics, specific job titles, "
        "companies, tools used, and tenure lengths.\n"
        "3. Highlight transferrable skills intelligently (e.g. if the candidate lacks Django but has FastAPI experience, note this transferability with evidence).\n"
        "4. Be transparent about gaps, risks, or overqualification flags.\n"
        "\n"
        "You must respond with a JSON object that matches the following schema:\n"
        "{\n"
        '  "overall_rank_summary": "1-2 sentences explaining exactly why this candidate scored what they did and where they stand relative to the JD requirements.",\n'
        '  "strengths": ["List of 2-4 concrete strengths, citing specific jobs, achievements, or project metrics. E.g. \'Demonstrated Postgres API capability by optimizing latency by 200ms at PaymentCorp.\'"],\n'
        '  "gaps_and_risks": ["List of 1-3 gaps/risks. E.g. \'Lacks direct React experience, although has Svelte background.\' or \'Total experience of 3.5 years is below the requested 5 years.\'"],\n'
        '  "concerns_flags": ["Recruiter flags, if any, explaining why they were raised (e.g. \'Job Hopper: average tenure is 1.1 years across 3 jobs\'). If none, return empty list."]\n'
        "}"
    )
    
    user_prompt = (
        f"Job Description Criteria:\n{json.dumps(jd_details, indent=2)}\n\n"
        f"Candidate Details:\n{json.dumps(cand_details, indent=2)}\n\n"
        f"Score Breakdown:\n{json.dumps(sub_scores_dict, indent=2)}\n\n"
        f"Calculated Score Alerts:\n{json.dumps(score_flags, indent=2)}"
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
        
        parsed_data = json.loads(response.choices[0].message.content)
        logger.debug(f"Explainability output: {parsed_data}")
        
        return CandidateRationale(**parsed_data)
        
    except Exception as e:
        logger.error(f"Error generating rationale: {e}")
        # Return structured fallback rationale on failure
        return CandidateRationale(
            overall_rank_summary=f"Candidate {candidate.name} matches domain requirements but faced an error during rationale generation.",
            strengths=[f"Holds technical background with skills: {', '.join(candidate.explicit_skills[:3])}"],
            gaps_and_risks=["Could not run deep analysis due to technical fallback."],
            concerns_flags=score_flags
        )

# Simple standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Quick mocks
    jd_intent = JobDescriptionIntent(
        role_title="Senior Fullstack Engineer",
        seniority_level="Senior",
        domain="Fullstack",
        must_have_skills=["Python", "React", "Postgres"],
        nice_to_have_skills=["Docker", "AWS"],
        implied_soft_skills=["ownership"],
        min_years_experience=5,
        summary="Seeking senior developer with strong Python/React backgrounds."
    )
    
    from src.models import WorkExperience
    mock_cand = CandidateProfile(
        candidate_id="test-1",
        name="Jane Fullstack",
        summary="Senior Developer designing React frontend and Python backend systems.",
        explicit_skills=["Python", "React", "Postgres"],
        inferred_skills=["Webpack"],
        experience=[
            WorkExperience(
                title="Lead Software Engineer",
                company="SaaS Corp",
                start_date="Jan 2022",
                end_date="Present",
                tenure_years=4.5,
                description="Built React dashboards and Python REST APIs. Optimized loading speeds by 30%.",
                inferred_skills=["React", "Python"],
                growth_signals=["Promoted from Senior Engineer"],
                scope_of_ownership="React Dashboard and Core REST API backend",
                achievement_language="Optimized loading speeds by 30%",
                is_relevant=True
            )
        ],
        behavioral_summary="Demonstrates high ownership.",
        overall_tenure_years=4.5,
        avg_tenure_years=4.5,
        growth_trajectory="steady promotion"
    )
    
    test_subscores = SubScores(
        semantic_score=85.0,
        skills_score=100.0,
        experience_score=90.0,
        trajectory_score=95.0
    )
    
    rationale = generate_candidate_rationale(jd_intent, mock_cand, test_subscores, ["Experience Gap: 4.5 years is slightly below the 5 years requirement."])
    print("Generated Rationale:")
    print(rationale.model_dump_json(indent=2))
