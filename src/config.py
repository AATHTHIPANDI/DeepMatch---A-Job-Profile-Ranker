import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# API Keys and Model configs
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Default scoring weights (totaling 1.0)
DEFAULT_WEIGHTS = {
    "semantic": 0.30,
    "skills": 0.30,
    "experience": 0.20,
    "trajectory": 0.20
}

# Transferable skills mapping groups
TRANSFERABLE_SKILLS = {
    "python_backend": ["django", "fastapi", "flask", "pyramid", "tornado"],
    "frontend_frameworks": ["react", "vue", "svelte", "angular", "solidjs", "nextjs", "nuxt"],
    "deep_learning": ["pytorch", "tensorflow", "keras", "jax", "mxnet"],
    "data_manipulation": ["pandas", "numpy", "polars", "dask"],
    "sql_databases": ["postgresql", "postgres", "mysql", "mariadb", "sqlite", "oracle", "sql server"],
    "nosql_databases": ["mongodb", "redis", "cassandra", "dynamodb", "elasticsearch", "neo4j"],
    "cloud_platforms": ["aws", "gcp", "google cloud", "azure", "oracle cloud"],
    "containerization": ["docker", "kubernetes", "podman", "k8s", "nomad"],
    "iac": ["terraform", "ansible", "pulumi", "cloudformation"]
}
