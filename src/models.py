from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class JobDescriptionIntent(BaseModel):
    role_title: str = Field(..., description="Calculated title of the job description")
    seniority_level: str = Field(..., description="Target seniority (Junior, Mid, Senior, Lead, Principal, Director/VP)")
    domain: str = Field(..., description="Primary domain of the job (e.g., Backend, Frontend, Fullstack, Data, DevOps, Mobile)")
    must_have_skills: List[str] = Field(default_factory=list, description="Must-have core technical skills or concepts")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Nice-to-have secondary skills or tools")
    implied_soft_skills: List[str] = Field(default_factory=list, description="Implied soft requirements, e.g., adaptability, collaboration")
    min_years_experience: Optional[int] = Field(None, description="Required minimum years of experience")
    summary: str = Field(..., description="Extracted semantic summary of what this role entails")

class WorkExperience(BaseModel):
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    start_date: str = Field(..., description="Start date of employment")
    end_date: str = Field(..., description="End date or 'Present'")
    tenure_years: float = Field(..., description="Calculated length of employment in years")
    description: str = Field(..., description="Raw text description of accomplishments and duties")
    inferred_skills: List[str] = Field(default_factory=list, description="Skills inferred from project descriptions")
    growth_signals: List[str] = Field(default_factory=list, description="Signals showing career growth (e.g., promotions, increasing scope)")
    scope_of_ownership: str = Field("", description="Scale and depth of responsibilities (e.g., led 4 people, owned database migration)")
    achievement_language: str = Field("", description="Action verbs and quantifiable metrics (e.g., optimized page load by 40%)")
    is_relevant: bool = Field(True, description="Whether this job is relevant to the target role domain")

class PlatformActivity(BaseModel):
    github_commits_past_year: Optional[int] = Field(None, description="Mocked commits in past year")
    github_repo_relevance: Optional[float] = Field(None, description="Similarity score of candidate's repos to target JD")
    linkedin_activity_recency: Optional[str] = Field(None, description="Mocked LinkedIn activity (active, inactive, none)")
    stackoverflow_reputation: Optional[int] = Field(None, description="Mocked StackOverflow reputation")

class CandidateProfile(BaseModel):
    candidate_id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Full name")
    contact: Dict[str, str] = Field(default_factory=dict, description="Contact information")
    summary: str = Field(..., description="Resume summary or profile bio")
    explicit_skills: List[str] = Field(default_factory=list, description="Skills explicitly listed in the skills section")
    inferred_skills: List[str] = Field(default_factory=list, description="Skills inferred across all experiences")
    experience: List[WorkExperience] = Field(default_factory=list, description="Chronological work history")
    behavioral_summary: str = Field("", description="Extracted trajectory, scope, and ownership patterns")
    overall_tenure_years: float = Field(0.0, description="Total years of work experience")
    avg_tenure_years: float = Field(0.0, description="Average tenure per job in years")
    growth_trajectory: str = Field("stable", description="Visualized trajectory (rapid growth, lateral, stagnant, job-hopping)")
    platform_activity: Optional[PlatformActivity] = Field(None, description="Optional platform metrics")

class SubScores(BaseModel):
    semantic_score: float = Field(..., description="Semantic alignment between candidate summary/experience and JD (0-100)")
    skills_score: float = Field(..., description="Direct must-have and nice-to-have skill match overlap (0-100)")
    experience_score: float = Field(..., description="Seniority, tenure, and recency alignment (0-100)")
    trajectory_score: float = Field(..., description="Growth signals, stability, achievement indicators (0-100)")

class CandidateRationale(BaseModel):
    overall_rank_summary: str = Field(..., description="Executive summary explaining candidate's fit and rank")
    strengths: List[str] = Field(default_factory=list, description="Strengths grounded directly in candidate profile evidence")
    gaps_and_risks: List[str] = Field(default_factory=list, description="Missing requirements or risk indicators (e.g. tenure, skill gaps)")
    concerns_flags: List[str] = Field(default_factory=list, description="Recruiter flags (e.g., job hopping, overqualification, location mismatch)")

class ShortlistedCandidate(BaseModel):
    candidate_id: str
    name: str
    overall_score: float = Field(..., description="Weighted composite score of the candidate (0-100)")
    sub_scores: SubScores
    rationale: CandidateRationale
    candidate_profile_snapshot: CandidateProfile

class ShortlistOutput(BaseModel):
    jd_intent: JobDescriptionIntent
    shortlist: List[ShortlistedCandidate]
