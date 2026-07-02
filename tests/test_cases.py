# Mock data representing 1 Job Description and 8 diverse Candidate profiles

SAMPLE_JD_TEXT = """
Role: Senior Backend Engineer (Python & PostgreSQL)
Hiring Team: Fintech core ledger team

We are looking for a Senior Backend Engineer to join our core ledger team. You will be responsible for building, optimizing, and maintaining backend APIs that process financial transactions securely.

Must-Have Requirements:
- 5+ years of software engineering experience.
- Deep expertise in Python and writing robust backend API services (Django or FastAPI).
- Advanced knowledge of SQL databases, specifically PostgreSQL (writing complex queries, query optimization, indexing).
- Strong ownership mindset - you will own services end-to-end and mentor junior engineers.

Nice-to-Have Requirements:
- Familiarity with Docker and containerized deployment.
- Experience with cloud platforms (preferably AWS).
- Implemented transaction isolation or dealt with ledger consistency challenges in previous roles.

Implied soft skills: Collaboration across teams, high-ownership, adaptability to fast-paced fintech domain.
"""

SAMPLE_CANDIDATES = [
    {
        "candidate_id": "cand-001",
        "name": "Alex Strong (Strong Fit)",
        "contact": {"email": "alex.strong@example.com", "phone": "555-0101"},
        "summary": "Senior Backend Engineer with 6+ years of experience designing robust API services in Python. Passionate about database optimization and fintech ledger consistency.",
        "skills": ["Python", "Django", "PostgreSQL", "Docker", "AWS", "SQL", "Git", "REST APIs"],
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "FintechScale",
                "start_date": "Jan 2023",
                "end_date": "Present",
                "description": "Led backend ledger redesign. Optimized PostgreSQL indexing and query execution plans, reducing transactional API latency by 45%. Mentored 3 junior developers and owned end-to-end ledger services."
            },
            {
                "title": "Software Engineer II",
                "company": "PayTech Solutions",
                "start_date": "Mar 2020",
                "end_date": "Dec 2022",
                "description": "Developed REST APIs using Python and Django. Implemented Docker containerization for core APIs and migrated services to AWS ECS."
            }
        ],
        "platform_activity": {
            "github_commits_past_year": 180,
            "github_repo_relevance": 0.95,
            "linkedin_activity_recency": "active",
            "stackoverflow_reputation": 1200
        }
    },
    {
        "candidate_id": "cand-002",
        "name": "Jamie Transferable (Partial Fit - Transferable Skills)",
        "contact": {"email": "jamie.transferable@example.com"},
        "summary": "Software Engineer focused on backend architecture. Expert in Node.js and REST APIs with a strong background in transactional databases.",
        "skills": ["JavaScript", "Node.js", "Express", "MongoDB", "MySQL", "Docker", "Redis"],
        "experience": [
            {
                "title": "Backend Engineer",
                "company": "SaaS Billing Inc",
                "start_date": "Jan 2021",
                "end_date": "Present",
                "description": "Designed transaction billing APIs in Node.js/Express. Managed billing ledger consistency using MySQL with strict ACID isolation levels. Implemented Docker for localized workflows."
            }
        ],
        "platform_activity": {
            "github_commits_past_year": 95,
            "github_repo_relevance": 0.50,
            "linkedin_activity_recency": "active",
            "stackoverflow_reputation": 200
        }
    },
    {
        "candidate_id": "cand-003",
        "name": "Taylor Keyword (Keyword Stuffing False Positive)",
        "contact": {"email": "taylor.keyword@example.com"},
        "summary": "Senior Python Python Developer Developer. Passionate about Django Django Django Postgres PostgreSQL PostgreSQL Docker Docker. Senior Python backend developer.",
        "skills": ["Python", "Django", "PostgreSQL", "Docker", "AWS", "SQL", "Git", "REST APIs"],
        "experience": [
            {
                "title": "Junior Python Developer",
                "company": "WebShop Co",
                "start_date": "Jul 2025",
                "end_date": "Present",
                "description": "Helped write Python scripts and assisted in maintaining Django endpoints. Used Postgres database for storing logs and ran Docker containers locally."
            }
        ],
        "platform_activity": {
            "github_commits_past_year": 15,
            "github_repo_relevance": 0.88,
            "linkedin_activity_recency": "inactive",
            "stackoverflow_reputation": 10
        }
    },
    {
        "candidate_id": "cand-004",
        "name": "Jordan Overqualified (Overqualified)",
        "contact": {"email": "jordan.overqualified@example.com"},
        "summary": "Principal Software Architect & former Director of Engineering. Over 15 years leading high-throughput transaction ledger architectures and managing large developer divisions.",
        "skills": ["Python", "PostgreSQL", "System Architecture", "Scalability", "AWS", "Kubernetes", "Engineering Management"],
        "experience": [
            {
                "title": "Director of Engineering",
                "company": "MegaBank Fintech",
                "start_date": "Mar 2022",
                "end_date": "Present",
                "description": "Managed 4 teams of backend and platform engineers (40+ developers). Oversaw architecture roadmap for high-frequency trading ledger using Python, PostgreSQL, and AWS."
            },
            {
                "title": "Principal Architect",
                "company": "PayGlobal",
                "start_date": "Jan 2018",
                "end_date": "Feb 2022",
                "description": "Designed transaction matching engines processing 50k transactions/sec. Wrote Python data aggregation pipelines and optimized Postgres vacuuming/partitioning policies."
            }
        ],
        "platform_activity": {
            "github_commits_past_year": 40,
            "github_repo_relevance": 0.90,
            "linkedin_activity_recency": "active",
            "stackoverflow_reputation": 4500
        }
    },
    {
        "candidate_id": "cand-005",
        "name": "Casey Weak (Weak Fit)",
        "contact": {"email": "casey.weak@example.com"},
        "summary": "Desktop Application Developer specializing in C++ and Java with 8 years experience building local GUI software.",
        "skills": ["C++", "Java", "Qt", "Swing", "SQLite", "Multi-threading"],
        "experience": [
            {
                "title": "C++ Engineer",
                "company": "DesktopSoft",
                "start_date": "Sep 2018",
                "end_date": "Present",
                "description": "Developed GUI dashboard tools in C++ using Qt. Handled local database interactions utilizing SQLite."
            }
        ],
        "platform_activity": {
            "github_commits_past_year": 12,
            "github_repo_relevance": 0.10,
            "linkedin_activity_recency": "none",
            "stackoverflow_reputation": 150
        }
    },
    {
        "candidate_id": "cand-006",
        "name": "Morgan Degraded (Graceful Degradation Case)",
        "contact": {"email": "morgan.degraded@example.com"},
        "summary": "Senior Backend Developer with 5.5 years experience writing APIs in Python and working with relational databases. Focuses on clean code and robust ledger services.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs"],
        "experience": [
            {
                "title": "Senior API Engineer",
                "company": "LedgerLine",
                "start_date": "Mar 2021",
                "end_date": "Present",
                "description": "Owned ledger API services built in FastAPI. Handled Postgres database schema designs and query optimizations. Set up Docker deployment scripts."
            }
        ],
        "platform_activity": {} # Empty - to test graceful degradation
    },
    {
        "candidate_id": "cand-007",
        "name": "Chris Hopper (Job Hopper)",
        "contact": {"email": "chris.hopper@example.com"},
        "summary": "Backend Developer with strong Python, Django, and PostgreSQL skills. Experienced working in highly agile fintech startups.",
        "skills": ["Python", "Django", "PostgreSQL", "AWS", "Docker"],
        "experience": [
            {
                "title": "Backend Engineer",
                "company": "LedgerFast",
                "start_date": "Jan 2026",
                "end_date": "Present",
                "description": "Wrote Python APIs for a micro-ledger application using Django and Postgres."
            },
            {
                "title": "Software Developer",
                "company": "PaySplit",
                "start_date": "Jul 2025",
                "end_date": "Dec 2025",
                "description": "Maintained payment endpoints written in Python."
            },
            {
                "title": "Junior Backend Dev",
                "company": "FinSprint",
                "start_date": "Jan 2025",
                "end_date": "Jun 2025",
                "description": "Assisted in writing Postgres queries for financial reports."
            },
            {
                "title": "Python Coder",
                "company": "CashFlow",
                "start_date": "Jul 2024",
                "end_date": "Dec 2024",
                "description": "Modified backend Python scripts and Django models."
            },
            {
                "title": "Junior Developer",
                "company": "FundNow",
                "start_date": "Jan 2024",
                "end_date": "Jun 2024",
                "description": "Fixed minor bugs in Python-based web applications."
            }
        ],
        "platform_activity": {
            "github_commits_past_year": 220,
            "github_repo_relevance": 0.90,
            "linkedin_activity_recency": "active",
            "stackoverflow_reputation": 300
        }
    },
    {
        "candidate_id": "cand-008",
        "name": "Sam TechMismatch (Domain Match, Tech Mismatch)",
        "contact": {"email": "sam.techmismatch@example.com"},
        "summary": "Senior Backend Developer in Fintech ledger divisions with 6 years experience. Expert in Spring Boot and highly distributed cloud databases.",
        "skills": ["Java", "Spring Boot", "Oracle DB", "Kubernetes", "Azure", "Microservices"],
        "experience": [
            {
                "title": "Senior Ledger Engineer",
                "company": "StateBank Fintech",
                "start_date": "Jan 2021",
                "end_date": "Present",
                "description": "Led backend architecture for high-security distributed ledger systems using Java and Spring Boot. Handled transaction consistency over Oracle DB."
            }
        ],
        "platform_activity": {
            "github_commits_past_year": 110,
            "github_repo_relevance": 0.20,
            "linkedin_activity_recency": "active",
            "stackoverflow_reputation": 800
        }
    }
]
