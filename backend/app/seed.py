"""
Demo dataset: professional roles with scored candidates.

WARNING: Calling seed() DELETES ALL existing roles, resumes, scores, and chunks.
Use POST /api/seed after deploy (or locally) to reset to a clean showcase dataset.

Run: POST /api/seed  or  python -c "import asyncio; from app.seed import seed; asyncio.run(seed())"
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import delete, update

from app.database import async_session
from app.models.role import Role
from app.models.resume import Resume
from app.models.score import Score


def _slug(s: str) -> str:
    return s.lower().replace(" ", "_").replace("—", "").replace("/", "_")


def _dims_for_overall(overall: float) -> list[dict[str, Any]]:
    """Four scoring dimensions with plausible spread around overall."""
    o = max(1.0, min(10.0, overall))
    tech = round(min(10, max(1, o + 0.35)), 1)
    depth = round(min(10, max(1, o - 0.15)), 1)
    domain = round(min(10, max(1, o + 0.08)), 1)
    traj = round(min(10, max(1, o - 0.22)), 1)
    return [
        {
            "dimension": "Technical Skills",
            "score": tech,
            "evidence": ["Stack aligns with role requirements", "Projects show hands-on delivery"],
            "gaps": [] if tech >= 7.0 else ["Depth in a few niche tools still to verify"],
        },
        {
            "dimension": "Experience Depth",
            "score": depth,
            "evidence": ["Progressive scope across recent roles", "Ownership of meaningful outcomes"],
            "gaps": [] if depth >= 7.0 else ["Limited exposure at largest scale — probe in interview"],
        },
        {
            "dimension": "Domain Relevance",
            "score": domain,
            "evidence": ["Industry and problem space match the opening", "Terminology and metrics fit"],
            "gaps": [] if domain >= 7.0 else ["Some domain adjacency — confirm with hiring manager"],
        },
        {
            "dimension": "Career Trajectory",
            "score": traj,
            "evidence": ["Consistent growth in responsibility", "Clear narrative across roles"],
            "gaps": [] if traj >= 7.0 else ["Trajectory still early — fine for mid-level roles"],
        },
    ]


def _rec_for_score(overall: float) -> str:
    if overall >= 8.2:
        return "strongly_recommend"
    if overall >= 7.0:
        return "recommend"
    if overall >= 5.5:
        return "maybe"
    return "do_not_advance"


def _confidence_for_score(overall: float) -> str:
    if overall <= 4.5 or overall >= 8.0:
        return "high"
    if overall <= 6.0:
        return "medium"
    return "high"


def build_candidate(
    role_title: str,
    role_key: str,
    idx: int,
    full_name: str,
    current_title: str,
    years: int,
    skills: list[str],
    education: str,
    summary: str,
    overall: float,
) -> dict[str, Any]:
    rec = _rec_for_score(overall)
    conf = _confidence_for_score(overall)
    dims = _dims_for_overall(overall)
    email = f"{_slug(full_name.split()[0])}.{_slug(full_name.split()[-1])}@email.com"
    fn = f"{_slug(full_name)}_{role_key}_{idx}.pdf"

    strengths = [
        {"point": "Relevant hands-on experience", "evidence": f"{current_title} background maps to {role_title}."},
        {"point": "Clear skill footprint", "evidence": f"Key skills include {', '.join(skills[:4])}."},
    ]
    concerns = []
    if overall < 7.0:
        concerns.append(
            {
                "point": "Fit has gaps to validate",
                "evidence": "Score reflects uneven match vs. bar for the role.",
                "suggested_question": "Describe the most complex initiative you owned end-to-end.",
            }
        )
    if overall < 5.5:
        concerns.append(
            {
                "point": "Below typical bar for this level",
                "evidence": "Experience depth or stack alignment is limited vs. JD.",
                "suggested_question": "How would you ramp on our primary stack in 90 days?",
            }
        )

    recruiter_summary = (
        f"{full_name} ({current_title}, ~{years} yrs) shows an {overall:.1f}/10 alignment for {role_title}. "
        f"Recommendation: {rec.replace('_', ' ')}."
    )

    suggested = [
        {"question": "What outcome are you most proud of in your last role?", "addresses": "Impact & ownership"},
        {"question": "How do you collaborate across product, design, and stakeholders?", "addresses": "Communication"},
    ]
    if overall < 6.5:
        suggested.append(
            {"question": "Where do you feel your biggest learning curve would be for this team?", "addresses": "Risk areas"}
        )

    return {
        "filename": fn,
        "extracted_fields": {
            "full_name": {"value": full_name, "evidence": f"{full_name} — {current_title}", "confidence": "high"},
            "email": {"value": email, "evidence": email, "confidence": "high"},
            "current_title": {"value": current_title, "evidence": current_title, "confidence": "high"},
            "total_experience_years": {"value": years, "evidence": f"{years} years professional experience", "confidence": "high"},
            "skills": {"value": skills, "evidence": "Skills section and role bullets", "confidence": "high"},
            "education": {"value": education, "evidence": education, "confidence": "high"},
            "summary": {"value": summary, "evidence": summary[:120], "confidence": "medium"},
        },
        "score": {
            "overall_score": overall,
            "recommendation": rec,
            "confidence": conf,
            "dimensional_scores": dims,
            "strengths": strengths,
            "concerns": concerns,
            "recruiter_summary": recruiter_summary,
            "suggested_questions": suggested,
        },
        "ai_authorship_signal": "none" if overall >= 6.0 else "weak",
        "contradiction_flags": [],
    }


# --- Role definitions: title, JD, blind mode, age in days, optional quality report, candidate specs ---
# Each candidate spec: (full_name, job_title, years, skills, education_line, summary, overall_score)

ROLE_BLUEPRINTS: list[dict[str, Any]] = [
    {
        "title": "Senior Backend Engineer",
        "blind_mode": True,
        "created_days_ago": 9,
        "jd_text": """
Senior Backend Engineer — Platform

We're hiring a Senior Backend Engineer to evolve our core API platform: reliability, security, and velocity
for B2B customers in regulated industries.

Requirements:
- 5+ years building production backend services
- Strong Python (FastAPI or Django) and PostgreSQL
- Redis, messaging, and REST/GraphQL API design
- AWS or GCP, containers (Docker/Kubernetes)
- Care for observability, on-call hygiene, and incremental delivery

Nice to have: compliance-adjacent work (SOC 2, audit logs), experience mentoring engineers.
""".strip(),
        "jd_quality_report": {
            "flags": [
                {"flag": "Clarify on-call expectations and rotation", "severity": "info", "suggestion": "Add expected hours or rotation frequency."},
            ],
            "overall_quality": "good",
            "summary": "Solid technical bar; light touch on soft expectations.",
        },
        "candidates": [
            ("Priya Sharma", "Senior Software Engineer", 7, ["Python", "FastAPI", "PostgreSQL", "Redis", "Kubernetes", "AWS"],
             "B.Tech CS, IIT Delhi, 2017", "Scaled services for high-traffic e-commerce; strong API and data-layer design.", 8.4),
            ("Rahul Verma", "Software Engineer II", 5, ["Python", "Django", "PostgreSQL", "AWS", "Docker"],
             "B.E. Computer Engineering, VIT, 2019", "Backend engineer focused on payments and ledger systems.", 7.5),
            ("Neha Kapoor", "Staff Engineer", 10, ["Python", "Go", "PostgreSQL", "Kafka", "Kubernetes", "Terraform"],
             "B.Tech IT, NSIT, 2014", "Led platform migrations and SLO improvements across multiple teams.", 8.9),
            ("Karan Malhotra", "Backend Developer", 4, ["Java", "Spring Boot", "MySQL", "Docker"],
             "B.Sc. CS, Mumbai University, 2020", "Enterprise APIs and batch processing; considering stronger Python pivot.", 5.8),
            ("Ananya Iyer", "Full Stack Developer", 4, ["Node.js", "React", "PostgreSQL", "Python"],
             "B.Sc. IT, Mumbai University, 2020", "Product-focused engineer; Python secondary to Node.", 5.6),
            ("Deepak Nair", "Engineering Lead", 9, ["Python", "FastAPI", "PostgreSQL", "Redis", "Kubernetes", "AWS", "Terraform"],
             "B.Tech CS, NIT Trichy, 2015", "Payments and compliance platforms; led team of eight.", 9.0),
            ("Sneha Gupta", "Software Developer", 2, ["Python", "Django", "MySQL", "REST"],
             "B.Tech CS, Pune University, 2022", "Early-career developer on internal tooling.", 3.9),
            ("Vikram Singh", "Senior Backend Engineer", 6, ["Python", "Flask", "PostgreSQL", "Redis", "GCP"],
             "M.Tech CS, IIT Kanpur, 2018", "Data-intensive APIs and batch pipelines for analytics products.", 7.8),
            ("Meera Krishnan", "Principal Engineer", 12, ["Python", "Rust", "PostgreSQL", "Kubernetes", "AWS"],
             "B.E. ECE, BITS Pilani, 2012", "Architecture for multi-tenant SaaS; mentor to senior ICs.", 8.7),
            ("Arjun Desai", "Backend Engineer", 3, ["Python", "FastAPI", "MongoDB", "Docker", "Azure"],
             "B.Tech CS, Manipal, 2021", "Greenfield microservices and CI/CD adoption.", 6.4),
            ("Riya Sen", "Software Engineer", 5, ["Ruby", "Rails", "PostgreSQL", "Sidekiq", "AWS"],
             "B.A. Mathematics, St. Xavier's, 2019", "Strong web stack; limited Python — ramp expected.", 6.1),
            ("Aditya Rao", "Senior Software Engineer", 8, ["Python", "Django", "Celery", "PostgreSQL", "AWS"],
             "M.S. Software Engineering, Carnegie Mellon, 2016", "High-reliability workflows and third-party integrations.", 8.1),
            ("Pooja Nambiar", "Engineering Manager", 11, ["Python", "PostgreSQL", "Kubernetes", "GCP"],
             "B.Tech CS, CET, 2013", "Hands-on manager; still codes for critical paths.", 7.2),
            ("Harsh Patel", "Junior Backend Engineer", 1, ["Python", "FastAPI", "SQLite", "Docker"],
             "B.Tech CS, DA-IICT, 2023", "First production role; internship experience only.", 4.5),
            ("Lisa Fernandes", "Senior Backend Engineer", 6, ["Kotlin", "Spring", "PostgreSQL", "Kafka", "AWS"],
             "B.E. CS, COEP, 2018", "JVM-heavy shop; Python surface area smaller.", 6.8),
            ("Mohit Agarwal", "Software Engineer III", 7, ["Python", "FastAPI", "PostgreSQL", "Redis", "AWS", "Datadog"],
             "B.Tech CS, IIIT Hyderabad, 2017", "Observability champion; on-call primary.", 8.0),
        ],
    },
    {
        "title": "Full Stack Developer",
        "blind_mode": True,
        "created_days_ago": 7,
        "jd_text": """
Full Stack Developer — Product Engineering

Build customer-facing features end-to-end: React/Next.js UI, Node or Python services, and integrations.

Requirements:
- 3+ years full stack delivery in a product team
- React or similar SPA framework; TypeScript preferred
- REST APIs; SQL databases; Git and code review culture
- Comfort with cloud deploys (Vercel, AWS, or GCP)

You'll pair with design and PM, ship experiments, and instrument analytics.
""".strip(),
        "jd_quality_report": {
            "flags": [],
            "overall_quality": "good",
            "summary": "Clear product-engineering expectations.",
        },
        "candidates": [
            ("Sanjay Mehta", "Full Stack Engineer", 5, ["TypeScript", "React", "Next.js", "Node.js", "PostgreSQL", "Prisma"],
             "B.Tech CS, Thapar, 2019", "Owns features from Figma to production.", 7.9),
            ("Elena D'Souza", "Software Engineer", 4, ["React", "Redux", "Python", "FastAPI", "PostgreSQL"],
             "B.Sc. CS, Christ University, 2020", "Hybrid stack; React primary, Python services.", 7.1),
            ("Chris Paul", "Full Stack Developer", 6, ["JavaScript", "Vue.js", "Express", "MongoDB", "AWS"],
             "B.Tech IT, SRM, 2018", "Vue-heavy; willing to move to React ecosystem.", 6.5),
            ("Fatima Khan", "Senior Full Stack Engineer", 8, ["TypeScript", "React", "NestJS", "PostgreSQL", "Docker", "GCP"],
             "B.E. CS, PESIT, 2016", "Led rewrite of customer dashboard; strong TypeScript.", 8.3),
            ("Varun Iyer", "Full Stack Developer", 3, ["React", "Node.js", "MySQL", "Redis"],
             "B.Tech CS, PICT, 2021", "Startup experience; fast shipping mindset.", 6.9),
            ("Tamara Brooks", "Engineer II", 4, ["React", "Python", "Django", "PostgreSQL", "Cypress"],
             "BS CS, University of Washington, 2020", "US remote; overlap with team hours.", 7.4),
            ("Nikhil Bose", "Frontend-leaning Full Stack", 5, ["React", "Tailwind", "Node.js", "GraphQL"],
             "B.Tech ECE, Jadavpur, 2019", "Strong UI craft; backend depth moderate.", 6.7),
            ("Olivia Chen", "Software Developer", 2, ["React", "JavaScript", "Firebase"],
             "B.S. Informatics, UC Irvine, 2022", "Early career; limited SQL and backend scale.", 5.2),
            ("Rajeev Menon", "Staff Full Stack Engineer", 10, ["React", "TypeScript", "Go", "PostgreSQL", "Kubernetes"],
             "B.Tech CS, IIT Madras, 2014", "Platform + product features; mentorship.", 8.6),
            ("Sara Malik", "Full Stack Engineer", 4, ["Angular", "Java", "Spring", "Oracle"],
             "B.E. CS, DJ Sanghvi, 2020", "Enterprise stack; framework mismatch for React role.", 5.4),
        ],
    },
    {
        "title": "Product Manager",
        "blind_mode": True,
        "created_days_ago": 5,
        "jd_text": """
Product Manager — B2B SaaS

Own discovery and delivery for a workflow product used by mid-market teams.

Requirements:
- 4+ years product management in B2B SaaS or similar
- Strong discovery: interviewing users, framing problems, prioritization
- Data-informed decisions; comfort with SQL or analytics tools
- Stakeholder management with engineering and design

You'll define roadmap themes, write crisp specs, and measure adoption outcomes.
""".strip(),
        "jd_quality_report": {
            "flags": [{"flag": "Add success metrics for first 90 days", "severity": "info", "suggestion": "e.g. activation, NPS, or expansion targets."}],
            "overall_quality": "fair",
            "summary": "Good role definition; success metrics could be sharper.",
        },
        "candidates": [
            ("Amit Khanna", "Senior Product Manager", 7, ["Roadmapping", "SQL", "Amplitude", "Jira", "Discovery", "B2B SaaS"],
             "MBA, IIM Bangalore, 2017", "Led roadmap for collaboration suite; PLG motion.", 8.2),
            ("Julia Park", "Product Manager", 5, ["A/B testing", "Mixpanel", "Figma", "Scrum", "Enterprise sales feedback loops"],
             "BS Business, NYU, 2019", "PM for analytics module; technical depth with eng.", 7.6),
            ("Dhruv Saxena", "Associate PM", 2, ["User research", "Notion", "Linear", "Excel"],
             "B.Tech + PM cert, Great Lakes, 2022", "Rotational program; limited B2B depth.", 5.8),
            ("Karen Wu", "Group PM", 9, ["Strategy", "SQL", "Segment", "Sales alignment", "Pricing"],
             "MBA, Kellogg, 2015", "Multi-product portfolio; exec stakeholders.", 8.5),
            ("Imran Sheikh", "Technical PM", 6, ["API products", "Postman", "OpenAPI", "Python scripting", "Launch"],
             "B.Tech CS, IIT Roorkee, 2018", "Platform PM for developer-facing APIs.", 7.8),
            ("Sophie Laurent", "Product Manager", 4, ["B2C growth", "Instagram Ads insights", "Looker"],
             "Masters Marketing, HEC Paris, 2020", "Strong analytics; B2C not B2B workflow.", 6.0),
            ("George Mathews", "Principal PM", 11, ["OKRs", "SQL", "Compliance workflows", "Enterprise rollout"],
             "BTech + MS, Georgia Tech, 2013", "Regulated industry launches; stakeholder-heavy.", 8.4),
            ("Keerthi Raman", "Product Owner", 5, ["Agile", "Azure DevOps", "Confluence", "Banking domain"],
             "B.E. ECE, Anna University, 2019", "Waterfall-to-agile transition in enterprise.", 6.9),
        ],
    },
    {
        "title": "Data Scientist",
        "blind_mode": True,
        "created_days_ago": 6,
        "jd_text": """
Data Scientist — Applied ML

Ship models and analyses that improve customer outcomes: churn, conversion, and operational efficiency.

Requirements:
- MS or PhD in quantitative field OR equivalent experience
- Python, pandas, scikit-learn; experience with at least one deep learning framework
- SQL fluency; ability to productionize or partner with ML engineers
- Clear communication of uncertainty and business impact

We value experimentation, clean notebooks, and reproducible pipelines.
""".strip(),
        "jd_quality_report": {"flags": [], "overall_quality": "good", "summary": "Well-scoped DS role."},
        "candidates": [
            ("Rohan Deshpande", "Senior Data Scientist", 6, ["Python", "PyTorch", "SQL", "Spark", "Causal inference", "Airflow"],
             "M.S. Statistics, ISI Kolkata, 2018", "Ranking and recommendation systems in e-commerce.", 8.3),
            ("Claire Novak", "Data Scientist", 4, ["Python", "scikit-learn", "XGBoost", "BigQuery", "dbt"],
             "M.S. Data Science, Columbia, 2020", "Marketing mix and attribution modeling.", 7.5),
            ("Manish Joshi", "ML Engineer", 5, ["Python", "TensorFlow", "Kubernetes", "FastAPI", "GCP"],
             "B.Tech CS, IIT Guwahati, 2019", "Deploys models; stronger engineering than research.", 7.2),
            ("Laura Bennett", "Research Scientist", 3, ["PyTorch", "NLP", "Hugging Face", "Python"],
             "Ph.D. Computational Linguistics, Edinburgh, 2021", "Research-heavy; limited SQL for analytics.", 6.3),
            ("Keertana Subramanian", "Lead Data Scientist", 8, ["Python", "SQL", "Propensity models", "Vertex AI", "Explainability"],
             "M.Tech CS, IIT Bombay, 2016", "Credit risk and compliance use cases.", 8.7),
            ("Alan Foster", "Data Analyst", 2, ["SQL", "Tableau", "Python basics", "Excel"],
             "BBA Analytics, NMIMS, 2022", "Dashboards and ad hoc analysis; not modeling depth.", 4.8),
            ("Nandini R", "Data Scientist II", 4, ["Python", "LightGBM", "Snowflake", "Experimentation"],
             "M.Sc. Mathematics, Chennai Mathematical Institute, 2020", "A/B tests and uplift modeling.", 7.0),
            ("Zubin Mehta", "Applied Scientist", 7, ["Python", "Keras", "Computer vision", "AWS SageMaker"],
             "Ph.D. EE, Stanford, 2017", "CV pipelines; less tabular work.", 7.7),
            ("Harini V", "Junior Data Scientist", 1, ["Python", "pandas", "scikit-learn", "PostgreSQL"],
             "M.S. Applied Math, IIT Hyderabad, 2023", "First full role; strong academics.", 5.5),
        ],
    },
    {
        "title": "DevOps Engineer",
        "blind_mode": True,
        "created_days_ago": 4,
        "jd_text": """
DevOps Engineer — Cloud Platform

Improve CI/CD, infrastructure as code, and reliability for a multi-service SaaS.

Requirements:
- 3+ years with AWS or GCP core services
- Terraform or Pulumi; Kubernetes operations
- CI/CD (GitHub Actions, GitLab, or Jenkins)
- Observability: metrics, logs, traces, alerting runbooks

On-call rotation with humane load; automating toil is a KPI.
""".strip(),
        "jd_quality_report": {"flags": [], "overall_quality": "good", "summary": "Clear SRE-leaning DevOps bar."},
        "candidates": [
            ("Sameer Khan", "Senior DevOps Engineer", 6, ["AWS", "Terraform", "Kubernetes", "Argo CD", "Prometheus", "Grafana"],
             "B.Tech IT, KJ Somaiya, 2018", "GitOps rollout and cost optimization initiatives.", 8.0),
            ("Tom Bradley", "Platform Engineer", 5, ["GCP", "GKE", "Helm", "Python", "Datadog"],
             "BS CS, UC San Diego, 2019", "Multi-cluster governance and guardrails.", 7.6),
            ("Divya S", "DevOps Engineer", 3, ["AWS", "Docker", "GitHub Actions", "Bash", "CloudFormation"],
             "B.E. CS, R.V. College, 2021", "Growing K8s depth; strong CI roots.", 6.6),
            ("Marcus Lee", "SRE", 7, ["Kubernetes", "Linkerd", "OpenTelemetry", "AWS", "PagerDuty"],
             "M.S. CS, UT Austin, 2017", "Incident management and error budgets.", 8.2),
            ("Ishaan Malik", "Cloud Engineer", 2, ["Azure", "ARM templates", "PowerShell", "Azure DevOps"],
             "B.Tech CS, IIIT Delhi, 2022", "Azure-first; AWS gap for this stack.", 5.7),
            ("Yuki Tanaka", "Staff Platform Engineer", 10, ["AWS", "Terraform", "EKS", "Service mesh", "FinOps"],
             "B.Eng., Tokyo Tech, 2014", "Global infra standardization; mentor for mid-levels.", 8.8),
            ("Peter D'Mello", "IT Operations", 8, ["VMware", "Windows Server", "Shell scripting", "Legacy DC"],
             "Diploma + BSc IT, Mumbai University, 2016", "Traditional ops; limited cloud-native IaC.", 4.9),
            ("Anjali Menon", "DevOps Engineer", 4, ["AWS", "Terraform", "Docker", "Jenkins", "Python"],
             "M.Tech CS, NIT Calicut, 2020", "CI pipelines and EC2/EKS hybrid migration.", 7.1),
        ],
    },
    {
        "title": "Machine Learning Engineer",
        "blind_mode": True,
        "created_days_ago": 3,
        "jd_text": """
Machine Learning Engineer — Production ML

Own training pipelines, model serving, and monitoring for NLP and ranking features.

Requirements:
- 4+ years shipping ML in production (batch and/or online)
- Python; PyTorch or TensorFlow; vector DB or embedding store experience
- Docker and Kubernetes; MLflow or similar experiment tracking
- Strong collaboration with data scientists and product

Nice to have: LLM fine-tuning, retrieval systems, cost/latency tradeoffs at scale.
""".strip(),
        "jd_quality_report": {
            "flags": [{"flag": "Clarify model SLAs (latency p99)", "severity": "info", "suggestion": "Add serving latency and availability targets."}],
            "overall_quality": "good",
            "summary": "Strong ML scope; serving SLOs would sharpen expectations.",
        },
        "candidates": [
            ("Kabir Anand", "ML Engineer", 5, ["Python", "PyTorch", "TorchServe", "Kubernetes", "Kafka", "MLflow"],
             "M.Tech CS, IIT Hyderabad, 2019", "Realtime ranking models with feature stores.", 8.1),
            ("Emily Carter", "Senior ML Engineer", 7, ["Python", "TensorFlow", "TF Serving", "GCP", "Triton"],
             "M.S. ML, Georgia Tech, 2017", "Large-scale batch + online inference.", 8.5),
            ("Satish Nair", "AI Engineer", 3, ["Python", "LangChain", "OpenAI API", "FastAPI", "Pinecone"],
             "B.Tech CS, NIT Calicut, 2021", "LLM apps; less traditional training pipelines.", 6.8),
            ("Ayesha Rahman", "Research Engineer", 4, ["PyTorch", "CUDA", "Distributed training", "W&B"],
             "M.S. EE, IIT Madras, 2020", "Training large models; serving exposure growing.", 7.3),
            ("David O'Neil", "Data Engineer", 5, ["Spark", "Airflow", "dbt", "Python", "AWS"],
             "BS CS, UT Austin, 2019", "Strong pipelines; lighter on model serving.", 6.2),
            ("Paridhi Jain", "Staff ML Engineer", 9, ["Python", "PyTorch", "Ray", "Kubernetes", "AWS", "GPU pools"],
             "B.Tech CS, IIT Kanpur, 2015", "End-to-end ML platform and governance.", 9.0),
            ("Lucas Ferreira", "ML Intern → Engineer", 2, ["Python", "scikit-learn", "Docker", "basic AWS"],
             "M.S. Data Science, CMU, 2022", "First production role post internship.", 5.1),
            ("Shruti Patil", "Applied ML Engineer", 6, ["Python", "Transformers", "ONNX", "Azure ML", "A/B testing"],
             "B.E. CS, COEP, 2018", "NLP features in customer support automation.", 7.9),
            ("Ben Carter", "Senior AI Engineer", 8, ["Python", "LLM fine-tuning", "LoRA", "vLLM", "Kubernetes"],
             "Ph.D. CS, UW-Madison, 2016", "Generative AI productization.", 8.6),
            ("Naveen Kulkarni", "ML Platform Engineer", 5, ["Python", "Kubeflow", "Argo", "Prometheus", "GKE"],
             "B.Tech CS, PICT, 2019", "Platform for training and deployment workflows.", 7.7),
        ],
    },
]


async def seed() -> None:
    """
    Replace all roles (and cascaded resumes, scores, chunks) with the curated demo dataset.
    """
    async with async_session() as db:
        # Clear self-referential duplicates so bulk delete never violates FK order.
        await db.execute(update(Resume).values(duplicate_of_id=None))
        await db.execute(delete(Role))
        await db.flush()

        for blueprint in ROLE_BLUEPRINTS:
            role_key = _slug(blueprint["title"])[:40]
            role = Role(
                id=uuid.uuid4(),
                title=blueprint["title"],
                jd_text=blueprint["jd_text"],
                blind_mode=blueprint["blind_mode"],
                status="active",
                jd_quality_report=blueprint.get("jd_quality_report"),
                created_at=datetime.now(timezone.utc) - timedelta(days=int(blueprint["created_days_ago"])),
            )
            db.add(role)
            await db.flush()

            specs = blueprint["candidates"]
            for i, spec in enumerate(specs):
                (full_name, job_title, years, skills, education, summary, overall) = spec
                candidate = build_candidate(
                    blueprint["title"],
                    role_key,
                    i,
                    full_name,
                    job_title,
                    years,
                    skills,
                    education,
                    summary,
                    float(overall),
                )
                upload_time = datetime.now(timezone.utc) - timedelta(hours=48 - i * 2)

                resume = Resume(
                    id=uuid.uuid4(),
                    role_id=role.id,
                    original_filename=candidate["filename"],
                    file_hash=f"seed_{role_key}_{i}_{uuid.uuid4().hex[:10]}",
                    parsed_text=f"[Demo resume — {candidate['extracted_fields']['full_name']['value']}]",
                    parse_report={
                        "confidence": 92,
                        "method": "demo_seed",
                        "sections_found": ["EXPERIENCE", "SKILLS", "EDUCATION"],
                        "warnings": [],
                    },
                    extracted_fields=candidate["extracted_fields"],
                    extraction_config_version=1,
                    contradiction_flags=candidate.get("contradiction_flags", []),
                    ai_authorship_signal=candidate.get("ai_authorship_signal", "none"),
                    status="scored",
                    uploaded_at=upload_time,
                )
                db.add(resume)
                await db.flush()

                s = candidate["score"]
                score = Score(
                    resume_id=resume.id,
                    role_id=role.id,
                    dimensional_scores=s["dimensional_scores"],
                    overall_score=s["overall_score"],
                    strengths=s["strengths"],
                    concerns=s["concerns"],
                    recruiter_summary=s["recruiter_summary"],
                    recommendation=s["recommendation"],
                    suggested_questions=s["suggested_questions"],
                    confidence=s["confidence"],
                    raw_scores={"dimensions": [{"dimension": d["dimension"], "score": round(d["score"] + 0.2, 1)} for d in s["dimensional_scores"]]},
                    critique={
                        "critiques": [
                            {
                                "dimension": d["dimension"],
                                "original_score": round(d["score"] + 0.2, 1),
                                "critique": "Adjusted after second-pass review of evidence density.",
                                "adjusted_score": d["score"],
                            }
                            for d in s["dimensional_scores"]
                        ]
                    },
                )
                db.add(score)

        await db.commit()
