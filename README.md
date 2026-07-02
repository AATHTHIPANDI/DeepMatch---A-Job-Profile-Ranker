# DeepMatch: AI-Powered Candidate Shortlisting System

DeepMatch is an advanced candidate ranking and shortlisting system designed to evaluate candidate profiles against Job Descriptions (JDs). It goes beyond simple keyword filtering by using semantic matching, multi-signal candidate representations, programmatic career trajectory metrics, and deep LLM explainability.

---

## 🏗️ System Architecture

```
                 +-----------------------------------------+
                 |          Raw Job Description            |
                 +-------------------+---------------------+
                                     |
                                     v
                        [ LLM JD Intent Parser ]
                                     |
                                     v
                 +-------------------+---------------------+
                 |         Structured JD Intent            |
                 |  Must/Nice Skills, Seniority, Domain    |
                 +-------------------+---------------------+
                                     |
                                     +-------------------------------+
                                     |                               |
                                     v                               v
+-------------------------+    +-----+--------------------+    +-----+-------------------+
| Raw Candidate Resumes  +---> | Candidate Synthesizer    +--->| Hybrid Scorer & Matcher |
+-------------------------+    | Calculates tenures,      |    | Calculates subscores &  |
                               | growth, scope, action    |    | compiles warnings/flags |
                               +--------------------------+    +-------------+-----------+
                                                                             |
                                                                             v
                                                                 [ LLM Rationale Generator ]
                                                                             |
                                                                             v
                                                               +-------------+-----------+
                                                               | Ranked Shortlist Output |
                                                               | (JSON + Styled HTML     |
                                                               |  + Streamlit Portal)    |
                                                               +-------------------------+
```

1. **Job Description Intent Parser**: Uses `llama-3.3-70b-versatile` via Groq in JSON mode to extract structured requirements (must-have/nice-to-have skills, target seniority level, domain, implied soft requirements, minimum years of experience).
2. **Candidate Synthesizer**: Focuses on parsing career timelines. It programmatically computes start/end date year fractions and job tenures (to prevent LLM math errors) and uses Groq to extract inferred skills, career growth velocity, scope of ownership, and action verbs/achievements.
3. **Hybrid Scorer**: Evaluates candidates by computing four sub-scores:
   - **Semantic Fit (30%)**: Cosine similarity between candidate career text and job description summary using local `all-MiniLM-L6-v2` SentenceTransformer embeddings (with Jaccard overlap fallback if model loading is unavailable).
   - **Skills Fit (30%)**: Matches must-have and nice-to-have skillsets. Uses a taxonomical mapping for **transferable skills** (e.g. counting FastAPI or Flask as a partial match for Django under a unified group).
   - **Experience Fit (20%)**: Distance matrix mapping target seniority level vs candidate current seniority, penalizing underqualified fits and flagging overqualified candidates, while checking years of experience and domain recency.
   - **Trajectory/Stability Fit (20%)**: Analyzes candidate growth signals, average job tenure duration, and incorporates optional platform enrichment signals (GitHub, LinkedIn) with graceful degradation when absent.
4. **Explainability Layer**: Converts numeric scores and flags into highly specific, evidence-grounded rationales. Vague filler words are banned; the LLM is forced to cite metrics, job titles, and achievements from the candidate's actual work history.

---

## 📈 Scoring Methodology & Weights Justification

We set standard weights that reflect a balanced screening process:
- **Semantic Relevance (30%)**: Evaluates overall domain relevance and context similarity.
- **Skills Overlap (30%)**: Ensures candidate possesses the exact technical stack or highly transferable alternatives.
- **Experience/Seniority (20%)**: Filters out juniors applying to senior roles and flags flight risks.
- **Trajectory/Behavioral (20%)**: Flags job-hoppers and rewards high-growth performers.

### Transferable Skills Logic
When a candidate lacks a direct skill, the matcher searches `TRANSFERABLE_SKILLS` in `src/config.py`. If the target skill shares a category (e.g. `postgresql` and `mysql` under `sql_databases`), the candidate is rewarded a **75% partial match** instead of 0%.

---

## ⚙️ How Explainability is Generated

Rather than relying on black-box scoring, DeepMatch feeds the candidate profile, JD intent, subscores, and calculated alerts to Groq (`llama-3.3-70b-versatile`). The system prompt enforces strict rules:
- Prohibits buzzwords (e.g., "fast learner").
- Requires citing direct evidence (e.g., *"Optimized latency by 45% at FintechScale"*).
- Separates findings into **Strengths**, **Gaps & Risks**, and **Recruiter Flags**.

---

## ⚠️ Limitations & Assumptions

1. **Mock Platform Data**: Optional LinkedIn and GitHub metrics are mocked via test case structures. The scorer handles empty inputs gracefully without scoring crashes (tested via Morgan Degraded case).
2. **Local Embedding Model**: Uses `all-MiniLM-L6-v2` which maps words into a 384-dimensional space. It is lightweight (90MB) but might miss complex domain vocabulary compared to massive commercial API embeddings.
3. **Antivirus Slowdowns**: On Windows, first-time virtual environment file writes or Hugging Face downloads can trigger slow file lock operations.

---

## 🚀 Setup & Execution

Follow these instructions to clone, install, and run the DeepMatch project.

### 1. Clone/Pull the Repository

Clone the repository to your local machine:
```bash
git clone https://github.com/your-username/DeepMatch.git
cd DeepMatch
```

If you already have it cloned and want to pull the latest updates:
```bash
git pull origin main
```

### 2. Configure Environment Variables

The project uses Groq Cloud API for JD parsing and explainability. 
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Create a Virtual Environment & Install Dependencies

It is highly recommended to use a virtual environment:

#### On Windows (PowerShell):
```powershell
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

#### On macOS/Linux:
```bash
# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Run the Project

You can run the application in two ways:

#### A. Web Portal (Streamlit App)
To launch the interactive UI dashboard:
```bash
streamlit run app.py
```
This will open the portal in your default web browser (typically at `http://localhost:8501`).

#### B. Command Line Interface (CLI Run & Tests)
To run the automated candidate shortlisting pipeline with the included test scenario:
```bash
python -m src.pipeline --run-tests
```
This runs the end-to-end matching process against built-in sample candidates and exports the results to:
- `shortlist.json` (Structured JSON scoring and rationales)
- `shortlist.html` (Styled web report format)

