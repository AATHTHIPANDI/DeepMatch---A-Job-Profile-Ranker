import os
import json
import logging
import argparse
import time
from typing import List, Dict, Any
from src.jd_parser import parse_job_description
from src.candidate_profile import synthesize_candidate_profile
from src.scorer import score_candidate
from src.explainability import generate_candidate_rationale
from src.models import ShortlistOutput, ShortlistedCandidate

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_shortlisting_pipeline(jd_text: str, raw_candidates: List[Dict[str, Any]]) -> ShortlistOutput:
    """
    Executes the end-to-end pipeline:
    1. Parses JD into structured intent
    2. Synthesizes each candidate profile
    3. Calculates hybrid scores
    4. Generates evidence-grounded explainability rationales
    5. Ranks and returns the ranked shortlist
    """
    logger.info("Starting candidate shortlisting pipeline...")
    
    # 1. Parse JD
    logger.info("Parsing Job Description...")
    jd_intent = parse_job_description(jd_text)
    logger.info(f"Successfully parsed JD: '{jd_intent.role_title}' ({jd_intent.seniority_level})")
    
    # 2. Process Candidates
    shortlisted_candidates = []
    
    for idx, raw_cand in enumerate(raw_candidates):
        cand_name = raw_cand.get("name", f"Candidate {idx+1}")
        logger.info(f"Synthesizing profile for {cand_name}...")
        
        # Synthesize profile
        profile = synthesize_candidate_profile(raw_cand)
        
        logger.info(f"Scoring {cand_name}...")
        # Calculate scores
        score, sub_scores, flags = score_candidate(jd_intent, profile)
        
        logger.info(f"Generating explainability rationale for {cand_name}...")
        # Generate rationale
        rationale = generate_candidate_rationale(jd_intent, profile, sub_scores, flags)
        
        shortlisted_candidates.append(ShortlistedCandidate(
            candidate_id=profile.candidate_id,
            name=profile.name,
            overall_score=score,
            sub_scores=sub_scores,
            rationale=rationale,
            candidate_profile_snapshot=profile
        ))
        
        # Sleep to avoid Groq Rate Limits
        time.sleep(1.2)
        
    # 3. Sort by overall score descending
    shortlisted_candidates.sort(key=lambda x: x.overall_score, reverse=True)
    
    logger.info("Shortlisting pipeline completed successfully.")
    return ShortlistOutput(
        jd_intent=jd_intent,
        shortlist=shortlisted_candidates
    )

def generate_html_report(output: ShortlistOutput, output_path: str):
    """Generates a premium-designed, highly visual HTML report for the recruiter."""
    
    jd = output.jd_intent
    candidates_html = ""
    
    for rank, cand in enumerate(output.shortlist):
        sub = cand.sub_scores
        rat = cand.rationale
        snap = cand.candidate_profile_snapshot
        
        # Color coding for overall score
        score_class = "score-high"
        if cand.overall_score < 50:
            score_class = "score-low"
        elif cand.overall_score < 75:
            score_class = "score-mid"
            
        # Compile lists
        strengths_li = "".join([f"<li>{s}</li>" for s in rat.strengths])
        gaps_li = "".join([f"<li>{g}</li>" for g in rat.gaps_and_risks])
        
        flags_html = ""
        if rat.concerns_flags:
            flags_li = "".join([f"<li>{f}</li>" for f in rat.concerns_flags])
            flags_html = f"""
            <div class="card-flags">
                <h4>Recruiter Flags / Concerns</h4>
                <ul>{flags_li}</ul>
            </div>
            """
            
        # Mocked or explicit skills tags
        skills_tags = "".join([f'<span class="tag">{s}</span>' for s in snap.explicit_skills[:8]])
        if len(snap.explicit_skills) > 8:
            skills_tags += f'<span class="tag tag-more">+{len(snap.explicit_skills)-8} more</span>'
            
        # Career progression snippet
        progression = " &rarr; ".join([job.title for job in reversed(snap.experience)])
        
        candidates_html += f"""
        <div class="candidate-card">
            <div class="card-header">
                <div class="header-left">
                    <span class="rank-badge">#{rank+1}</span>
                    <div>
                        <h3>{cand.name}</h3>
                        <p class="progression">{progression}</p>
                    </div>
                </div>
                <div class="header-right">
                    <div class="score-circle {score_class}">{cand.overall_score}</div>
                </div>
            </div>
            
            <div class="card-grid">
                <div class="grid-left">
                    <div class="sub-scores-section">
                        <h4>Fit Breakdown</h4>
                        <div class="bar-container">
                            <span class="bar-label">Semantic Match ({sub.semantic_score}%)</span>
                            <div class="bar-outer"><div class="bar-inner" style="width: {sub.semantic_score}%;"></div></div>
                        </div>
                        <div class="bar-container">
                            <span class="bar-label">Skills Match ({sub.skills_score}%)</span>
                            <div class="bar-outer"><div class="bar-inner" style="width: {sub.skills_score}%;"></div></div>
                        </div>
                        <div class="bar-container">
                            <span class="bar-label">Experience & Seniority ({sub.experience_score}%)</span>
                            <div class="bar-outer"><div class="bar-inner" style="width: {sub.experience_score}%;"></div></div>
                        </div>
                        <div class="bar-container">
                            <span class="bar-label">Trajectory & Stability ({sub.trajectory_score}%)</span>
                            <div class="bar-outer"><div class="bar-inner" style="width: {sub.trajectory_score}%;"></div></div>
                        </div>
                    </div>
                    
                    <div class="skills-section">
                        <h4>Key Skills</h4>
                        <div class="tags-container">
                            {skills_tags}
                        </div>
                    </div>
                </div>
                
                <div class="grid-right">
                    <div class="rationale-section">
                        <h4>Recruiter Rationale</h4>
                        <p class="rationale-text">"{rat.overall_rank_summary}"</p>
                    </div>
                    
                    <div class="bullet-grid">
                        <div class="bullets-strengths">
                            <h5>Key Strengths</h5>
                            <ul>{strengths_li}</ul>
                        </div>
                        <div class="bullets-gaps">
                            <h5>Gaps & Risks</h5>
                            <ul>{gaps_li}</ul>
                        </div>
                    </div>
                    
                    {flags_html}
                </div>
            </div>
        </div>
        """
        
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recruiter Shortlist Report: {jd.role_title}</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #090d16;
                --card-bg: #111827;
                --text: #f3f4f6;
                --text-muted: #9ca3af;
                --primary: #6366f1;
                --primary-glow: rgba(99, 102, 241, 0.15);
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --border: rgba(255, 255, 255, 0.08);
            }}
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                background-color: var(--bg);
                color: var(--text);
                font-family: 'Plus Jakarta Sans', sans-serif;
                line-height: 1.6;
                padding: 3rem 2rem;
            }}
            
            .container {{
                max-width: 1100px;
                margin: 0 auto;
            }}
            
            header {{
                margin-bottom: 3rem;
                border-bottom: 1px solid var(--border);
                padding-bottom: 2rem;
            }}
            
            .header-badge {{
                display: inline-block;
                background-color: var(--primary-glow);
                color: #818cf8;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.85rem;
                font-weight: 600;
                margin-bottom: 0.75rem;
                border: 1px solid rgba(99, 102, 241, 0.3);
            }}
            
            h1 {{
                font-family: 'Outfit', sans-serif;
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #fff, #9ca3af);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            
            .jd-summary-card {{
                background-color: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1.5rem;
                margin-top: 1.5rem;
            }}
            
            .jd-summary-card h3 {{
                font-family: 'Outfit', sans-serif;
                margin-bottom: 0.75rem;
                color: #818cf8;
            }}
            
            .jd-meta {{
                display: flex;
                gap: 1.5rem;
                margin-top: 1rem;
                font-size: 0.9rem;
                color: var(--text-muted);
            }}
            
            .jd-meta strong {{
                color: var(--text);
            }}
            
            .candidate-card {{
                background-color: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 2rem;
                margin-bottom: 2rem;
                position: relative;
                overflow: hidden;
                transition: transform 0.2s ease, border-color 0.2s ease;
            }}
            
            .candidate-card:hover {{
                border-color: rgba(99, 102, 241, 0.4);
                transform: translateY(-2px);
            }}
            
            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border);
                padding-bottom: 1.5rem;
                margin-bottom: 1.5rem;
            }}
            
            .header-left {{
                display: flex;
                align-items: center;
                gap: 1.25rem;
            }}
            
            .rank-badge {{
                font-family: 'Outfit', sans-serif;
                font-size: 1.5rem;
                font-weight: 700;
                color: #818cf8;
                background-color: var(--primary-glow);
                padding: 0.5rem 1rem;
                border-radius: 8px;
                border: 1px solid rgba(99, 102, 241, 0.2);
            }}
            
            .candidate-card h3 {{
                font-family: 'Outfit', sans-serif;
                font-size: 1.5rem;
                font-weight: 600;
            }}
            
            .progression {{
                font-size: 0.85rem;
                color: var(--text-muted);
                margin-top: 0.25rem;
            }}
            
            .score-circle {{
                font-family: 'Outfit', sans-serif;
                font-size: 1.8rem;
                font-weight: 700;
                width: 65px;
                height: 65px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 3px solid;
            }}
            
            .score-high {{
                color: var(--success);
                border-color: var(--success);
                background-color: rgba(16, 185, 129, 0.1);
            }}
            
            .score-mid {{
                color: var(--warning);
                border-color: var(--warning);
                background-color: rgba(245, 158, 11, 0.1);
            }}
            
            .score-low {{
                color: var(--danger);
                border-color: var(--danger);
                background-color: rgba(239, 68, 68, 0.1);
            }}
            
            .card-grid {{
                display: grid;
                grid-template-columns: 1fr 1.5fr;
                gap: 2rem;
            }}
            
            @media (max-width: 768px) {{
                .card-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            
            .sub-scores-section h4, 
            .skills-section h4,
            .rationale-section h4 {{
                font-family: 'Outfit', sans-serif;
                font-size: 1.05rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--text-muted);
                margin-bottom: 1rem;
            }}
            
            .bar-container {{
                margin-bottom: 1rem;
            }}
            
            .bar-label {{
                display: block;
                font-size: 0.85rem;
                color: var(--text-muted);
                margin-bottom: 0.25rem;
            }}
            
            .bar-outer {{
                height: 8px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                overflow: hidden;
            }}
            
            .bar-inner {{
                height: 100%;
                background-color: var(--primary);
                border-radius: 4px;
            }}
            
            .tags-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 0.5rem;
            }}
            
            .tag {{
                font-size: 0.75rem;
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--border);
                color: var(--text);
                padding: 0.2rem 0.6rem;
                border-radius: 4px;
            }}
            
            .tag-more {{
                color: var(--text-muted);
            }}
            
            .rationale-text {{
                font-style: italic;
                font-size: 1.05rem;
                color: #e5e7eb;
                line-height: 1.5;
                margin-bottom: 1.5rem;
                padding-left: 1rem;
                border-left: 3px solid var(--primary);
            }}
            
            .bullet-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1.5rem;
                margin-bottom: 1.5rem;
            }}
            
            @media (max-width: 600px) {{
                .bullet-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            
            .bullets-strengths h5 {{
                color: var(--success);
                font-size: 0.95rem;
                margin-bottom: 0.5rem;
                font-family: 'Outfit', sans-serif;
            }}
            
            .bullets-gaps h5 {{
                color: var(--warning);
                font-size: 0.95rem;
                margin-bottom: 0.5rem;
                font-family: 'Outfit', sans-serif;
            }}
            
            ul {{
                list-style-type: none;
            }}
            
            ul li {{
                font-size: 0.85rem;
                margin-bottom: 0.5rem;
                position: relative;
                padding-left: 1rem;
                color: #d1d5db;
            }}
            
            ul li::before {{
                content: "•";
                position: absolute;
                left: 0;
            }}
            
            .bullets-strengths ul li::before {{
                color: var(--success);
            }}
            
            .bullets-gaps ul li::before {{
                color: var(--warning);
            }}
            
            .card-flags {{
                background-color: rgba(239, 68, 68, 0.05);
                border: 1px solid rgba(239, 68, 68, 0.15);
                border-radius: 8px;
                padding: 1rem;
                margin-top: 1.5rem;
            }}
            
            .card-flags h4 {{
                font-family: 'Outfit', sans-serif;
                color: var(--danger);
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
            }}
            
            .card-flags ul li {{
                color: #fca5a5;
                font-size: 0.8rem;
            }}
            
            .card-flags ul li::before {{
                color: var(--danger);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <span class="header-badge">AI Shortlist Assistant</span>
                <h1>Candidate Shortlist Report</h1>
                <p style="color: var(--text-muted)">Ranked candidate profiles generated with evidence-based explanations</p>
                
                <div class="jd-summary-card">
                    <h3>Target Job Description: {jd.role_title}</h3>
                    <p style="font-size: 0.95rem; color: #d1d5db;">{jd.summary}</p>
                    <div class="jd-meta">
                        <div>Seniority Level: <strong>{jd.seniority_level}</strong></div>
                        <div>Target Domain: <strong>{jd.domain}</strong></div>
                        <div>Min Experience: <strong>{f"{jd.min_years_experience} years" if jd.min_years_experience else "None specified"}</strong></div>
                    </div>
                </div>
            </header>
            
            <main>
                {candidates_html}
            </main>
        </div>
    </body>
    </html>
    """
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"HTML report successfully written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="AI Candidate Shortlisting Pipeline")
    parser.add_argument("--run-tests", action="store_true", help="Runs standard pipeline test suite using mock data.")
    
    args = parser.parse_args()
    
    if args.run_tests:
        logger.info("Loading test scenario...")
        from tests.test_cases import SAMPLE_JD_TEXT, SAMPLE_CANDIDATES
        
        output = run_shortlisting_pipeline(SAMPLE_JD_TEXT, SAMPLE_CANDIDATES)
        
        # Write outputs
        json_output_path = os.path.join(os.getcwd(), "shortlist.json")
        html_output_path = os.path.join(os.getcwd(), "shortlist.html")
        
        # Convert output to dict and write to json file
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(output.model_dump(), f, indent=2)
        logger.info(f"JSON shortlist successfully written to {json_output_path}")
        
        generate_html_report(output, html_output_path)
        
        # Print a CLI table to prove correct discrimination
        print("\n" + "=" * 80)
        print("                 EVALUATION RUN: RANKED CANDIDATE RESULTS")
        print("=" * 80)
        print(f"{'Rank':<5} | {'Candidate Name':<50} | {'Score':<6} | {'Alerts Count':<12}")
        print("-" * 80)
        for rank, cand in enumerate(output.shortlist):
            alerts_count = len(cand.rationale.concerns_flags)
            print(f"#{rank+1:<4} | {cand.name:<50} | {cand.overall_score:<6} | {alerts_count:<12}")
        print("=" * 80)
        print("\nSanity Check Verification:")
        # Let's perform discrimination assertions programmatically:
        strong_cand = output.shortlist[0]
        keyword_cand = next(c for c in output.shortlist if "Taylor Keyword" in c.name)
        
        print(f"- Top candidate is: {strong_cand.name} (Score: {strong_cand.overall_score})")
        print(f"- Keyword-stuffed candidate ({keyword_cand.name}) scored: {keyword_cand.overall_score}")
        
        if strong_cand.candidate_id == "cand-001" and keyword_cand.overall_score < strong_cand.overall_score:
            print("\n[SUCCESS] Pipeline successfully discriminated! The strong candidate ranks higher than the keyword-stuffer.")
        else:
            print("\n[WARNING] Check scoring weights. Stuffer may have matched too closely.")

if __name__ == "__main__":
    main()
