import logging
import numpy as np
from typing import Dict, Any, List, Set, Tuple
from sentence_transformers import SentenceTransformer
from src.config import DEFAULT_WEIGHTS, TRANSFERABLE_SKILLS, EMBEDDING_MODEL
from src.models import JobDescriptionIntent, CandidateProfile, SubScores

logger = logging.getLogger(__name__)

# Initialize the embedding model globally
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            logger.info("Initializing SentenceTransformer embedding model...")
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}. Fallback to token similarity will be used.")
    return _embedding_model

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculates cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))

def get_token_overlap_similarity(text1: str, text2: str) -> float:
    """Fallback Jaccard token overlap similarity if embeddings fail."""
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

# Map seniority levels to numeric rank for distance calculations
SENIORITY_RANKS = {
    "intern": 0,
    "junior": 1,
    "mid": 2,
    "senior": 3,
    "lead": 4,
    "principal": 5,
    "director/vp": 6
}

def clean_skill(skill: str) -> str:
    return skill.strip().lower()

def check_skill_match(candidate_skills: Set[str], target_skill: str) -> Tuple[bool, float]:
    """
    Checks if a target skill matches a candidate's skill pool.
    Handles exact matches (1.0 weight) and transferable skills (0.8 weight).
    """
    target = clean_skill(target_skill)
    
    # 1. Direct match
    if target in candidate_skills:
        return True, 1.0
        
    # 2. Transferable skills group match
    for group_name, skills_in_group in TRANSFERABLE_SKILLS.items():
        clean_group_skills = [clean_skill(s) for s in skills_in_group]
        if target in clean_group_skills:
            # Check if candidate has ANY other skill in this same group
            matches = candidate_skills.intersection(clean_group_skills)
            if matches:
                logger.debug(f"Transferable skill match: candidate's {list(matches)} matched target '{target_skill}' via group '{group_name}'")
                return True, 0.75 # 75% score for transferable skills
                
    return False, 0.0

def score_candidate(jd: JobDescriptionIntent, candidate: CandidateProfile, custom_weights: Dict[str, float] = None) -> Tuple[float, SubScores, List[str]]:
    """
    Scores a candidate against a JD. Returns the overall score, subscore details, and a list of alerts/flags.
    """
    weights = custom_weights or DEFAULT_WEIGHTS
    flags = []
    
    # --- 1. Semantic Similarity Score (30%) ---
    semantic_score = 0.0
    model = get_embedding_model()
    
    # Candidate text footprint: summary + work experiences description
    candidate_footprint = f"{candidate.summary} " + " ".join([exp.description for exp in candidate.experience])
    jd_footprint = f"{jd.summary} " + " ".join(jd.must_have_skills + jd.nice_to_have_skills)
    
    if model:
        try:
            embs = model.encode([jd_footprint, candidate_footprint])
            sim = calculate_cosine_similarity(embs[0], embs[1])
            # Scale cosine similarity from [-1, 1] or [0, 1] range to [0, 100]
            semantic_score = max(0.0, min(100.0, sim * 100))
        except Exception as e:
            logger.error(f"Error during embedding generation: {e}")
            sim = get_token_overlap_similarity(jd_footprint, candidate_footprint)
            semantic_score = sim * 100
    else:
        sim = get_token_overlap_similarity(jd_footprint, candidate_footprint)
        semantic_score = sim * 100
        
    # --- 2. Skills Overlap Score (30%) ---
    # Merge explicit and inferred skills
    cand_skills_set = {clean_skill(s) for s in candidate.explicit_skills + candidate.inferred_skills}
    
    # Calculate must-have coverage
    must_have_matches = []
    must_have_weights = []
    for s in jd.must_have_skills:
        matched, weight = check_skill_match(cand_skills_set, s)
        must_have_matches.append(matched)
        must_have_weights.append(weight)
        
    must_have_score = sum(must_have_weights) / len(jd.must_have_skills) if jd.must_have_skills else 1.0
    
    # Calculate nice-to-have coverage
    nice_have_matches = []
    nice_have_weights = []
    for s in jd.nice_to_have_skills:
        matched, weight = check_skill_match(cand_skills_set, s)
        nice_have_matches.append(matched)
        nice_have_weights.append(weight)
        
    nice_have_score = sum(nice_have_weights) / len(jd.nice_to_have_skills) if jd.nice_to_have_skills else 1.0
    
    # Skills score is 80% must-haves + 20% nice-to-haves
    skills_score = (must_have_score * 0.8 + nice_have_score * 0.2) * 100
    
    # --- 3. Experience & Seniority Score (20%) ---
    experience_fit = 100.0
    
    # A. Seniority level match
    jd_rank_str = jd.seniority_level.lower()
    # Normalize JD ranks
    if "lead" in jd_rank_str:
        jd_rank = SENIORITY_RANKS["lead"]
    elif "senior" in jd_rank_str:
        jd_rank = SENIORITY_RANKS["senior"]
    elif "mid" in jd_rank_str or "software engineer" in jd_rank_str:
        jd_rank = SENIORITY_RANKS["mid"]
    elif "junior" in jd_rank_str:
        jd_rank = SENIORITY_RANKS["junior"]
    elif "principal" in jd_rank_str or "staff" in jd_rank_str:
        jd_rank = SENIORITY_RANKS["principal"]
    elif "director" in jd_rank_str or "vp" in jd_rank_str:
        jd_rank = SENIORITY_RANKS["director/vp"]
    else:
        jd_rank = SENIORITY_RANKS["mid"]
        
    # Match candidate growth trajectory or latest job title to determine candidate rank
    cand_latest_title = candidate.experience[0].title.lower() if candidate.experience else ""
    cand_rank = SENIORITY_RANKS["mid"] # default
    for rank_name, rank_val in SENIORITY_RANKS.items():
        if rank_name in cand_latest_title:
            cand_rank = rank_val
            break
            
    rank_diff = cand_rank - jd_rank
    
    # Rank deductions
    if rank_diff < 0:
        # Underqualified (candidate has lower level than role)
        # Deduct 25 points per level deficit
        experience_fit -= abs(rank_diff) * 25
        flags.append(f"Underqualification Risk: Candidate is at {list(SENIORITY_RANKS.keys())[cand_rank]} level but role requires {jd.seniority_level}.")
    elif rank_diff > 1:
        # Overqualified (candidate is 2+ levels higher)
        experience_fit -= 15 # small deduction to penalize flight risk
        flags.append(f"Overqualification Risk: Candidate operates at {list(SENIORITY_RANKS.keys())[cand_rank]} level which exceeds the requested {jd.seniority_level}.")
        
    # B. Years of experience check
    if jd.min_years_experience:
        if candidate.overall_tenure_years < jd.min_years_experience:
            deficit = jd.min_years_experience - candidate.overall_tenure_years
            # Deduct 10 points per year of deficit, max deduction 40
            experience_fit -= min(40.0, deficit * 10)
            flags.append(f"Experience Gap: Has {candidate.overall_tenure_years} years of total experience, missing the {jd.min_years_experience} years requirement.")
            
    # C. Recency of relevant experience (is their latest job relevant to the domain?)
    if candidate.experience:
        latest_job = candidate.experience[0]
        # Check if latest job title matches JD domain keywords
        domain_keywords = [jd.domain.lower(), "engineer", "developer", "programmer", "architect"]
        latest_title_lower = latest_job.title.lower()
        has_domain_match = any(kw in latest_title_lower for kw in domain_keywords)
        
        if not has_domain_match and not latest_job.is_relevant:
            experience_fit -= 15
            flags.append("Recency Concern: Latest role is outside of targeted engineering/domain focus.")
            
    experience_score = max(0.0, min(100.0, experience_fit))
    
    # --- 4. Trajectory & Behavioral Score (20%) ---
    trajectory_fit = 100.0
    
    # A. Growth Trajectory deduction / bonus
    trajectory_lower = candidate.growth_trajectory.lower()
    if "rapid growth" in trajectory_lower:
        trajectory_fit += 10 # bonus for high performance indicators
    elif "steady" in trajectory_lower or "promotion" in trajectory_lower:
        trajectory_fit += 5
    elif "stagnant" in trajectory_lower or "lateral" in trajectory_lower:
        trajectory_fit -= 10
    elif "job-hopping" in trajectory_lower or "unstable" in trajectory_lower:
        trajectory_fit -= 25
        flags.append("Job Hopping: Career trajectory indicates instability / short job durations.")
        
    # B. Average tenure check
    if candidate.avg_tenure_years < 1.2 and len(candidate.experience) >= 3:
        trajectory_fit -= 15
        if "Job Hopping" not in [f.split(":")[0] for f in flags]:
            flags.append(f"Short Tenure: Average job stay is low ({candidate.avg_tenure_years} years).")
            
    # C. Platform activity bonus/degradation
    # ( optional signals: degrade gracefully if absent, add small bonuses if present )
    if candidate.platform_activity:
        pa = candidate.platform_activity
        bonus = 0.0
        if pa.github_commits_past_year and pa.github_commits_past_year > 100:
            bonus += 5.0
        if pa.github_repo_relevance and pa.github_repo_relevance > 0.8:
            bonus += 5.0
        if pa.linkedin_activity_recency == "active":
            bonus += 2.0
            
        trajectory_fit += bonus
        
    trajectory_score = max(0.0, min(100.0, trajectory_fit))
    
    # --- Overall Score Calculation ---
    overall_score = (
        (semantic_score * weights["semantic"]) +
        (skills_score * weights["skills"]) +
        (experience_score * weights["experience"]) +
        (trajectory_score * weights["trajectory"])
    )
    
    sub_scores = SubScores(
        semantic_score=round(semantic_score, 2),
        skills_score=round(skills_score, 2),
        experience_score=round(experience_score, 2),
        trajectory_score=round(trajectory_score, 2)
    )
    
    return round(overall_score, 2), sub_scores, flags

# Simple standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Quick mocks to test
    jd_intent = JobDescriptionIntent(
        role_title="Senior Python Engineer",
        seniority_level="Senior",
        domain="Backend",
        must_have_skills=["Python", "Django", "Postgres"],
        nice_to_have_skills=["Docker", "AWS"],
        implied_soft_skills=["ownership"],
        min_years_experience=5,
        summary="Looking for a backend developer experienced in Python and Django."
    )
    
    from src.models import WorkExperience
    mock_cand = CandidateProfile(
        candidate_id="test-1",
        name="John Backend",
        summary="Senior Backend Engineer writing Python APIs for fintech.",
        explicit_skills=["Python", "FastAPI", "Postgres", "Docker"],
        inferred_skills=["REST APIs"],
        experience=[
            WorkExperience(
                title="Senior Developer",
                company="FinBank",
                start_date="Jan 2021",
                end_date="Present",
                tenure_years=5.5,
                description="Designed Python backend API services using FastAPI and Postgres.",
                inferred_skills=["FastAPI"],
                growth_signals=["Promoted from Mid Developer"],
                scope_of_ownership="Payments backend",
                achievement_language="handled 10k transactions/sec",
                is_relevant=True
            )
        ],
        behavioral_summary="Solid background.",
        overall_tenure_years=5.5,
        avg_tenure_years=5.5,
        growth_trajectory="steady promotion"
    )
    
    score, breakdown, alerts = score_candidate(jd_intent, mock_cand)
    print(f"Overall Score: {score}")
    print(f"Breakdown: {breakdown.model_dump_json(indent=2)}")
    print(f"Alerts: {alerts}")
