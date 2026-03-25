"""
Seed database with a sample role and pre-scored candidates for instant demo.
Run: POST /api/seed  or  python -c "import asyncio; from app.seed import seed; asyncio.run(seed())"
"""
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.database import async_session
from app.models.role import Role
from app.models.resume import Resume
from app.models.score import Score

SAMPLE_JD = """
Senior Backend Engineer — Sprinto

About the Role:
We're looking for a Senior Backend Engineer to join our core platform team. You'll build and scale the compliance automation systems used by thousands of companies globally.

Requirements:
- 5+ years of backend engineering experience
- Strong proficiency in Python (FastAPI, Django, or Flask)
- Experience with PostgreSQL and Redis
- Familiarity with cloud infrastructure (AWS, GCP, or Azure)
- Experience building REST APIs and microservices
- Understanding of security and compliance concepts (SOC 2, ISO 27001) is a plus
- Experience with Docker and Kubernetes
- Strong problem-solving skills and attention to detail

Nice to Have:
- Experience with AI/ML integrations
- Prior experience at a B2B SaaS company
- Contributions to open-source projects

What You'll Do:
- Design and implement scalable backend services
- Collaborate with product and frontend teams
- Improve system reliability and performance
- Mentor junior engineers
"""

CANDIDATES = [
    {
        "filename": "priya_sharma_senior_backend.pdf",
        "extracted_fields": {
            "full_name": {"value": "Priya Sharma", "evidence": "Priya Sharma — Senior Software Engineer", "confidence": "high"},
            "email": {"value": "priya.sharma@email.com", "evidence": "priya.sharma@email.com", "confidence": "high"},
            "current_title": {"value": "Senior Software Engineer", "evidence": "Senior Software Engineer — Flipkart", "confidence": "high"},
            "total_experience_years": {"value": 7, "evidence": "7 years across 3 roles", "confidence": "high"},
            "skills": {"value": ["Python", "FastAPI", "PostgreSQL", "Redis", "Kubernetes", "AWS"], "evidence": "Python, FastAPI, PostgreSQL, Redis, Kubernetes, AWS in Skills section", "confidence": "high"},
            "education": {"value": "B.Tech Computer Science, IIT Delhi, 2017", "evidence": "B.Tech CS, IIT Delhi (2017)", "confidence": "high"},
            "summary": {"value": "7 years backend engineering, Python specialist, scaled systems to 50M req/day", "evidence": "scaled microservices to 50M req/day at Flipkart", "confidence": "high"},
        },
        "score": {
            "overall_score": 8.2,
            "recommendation": "strongly_recommend",
            "confidence": "high",
            "dimensional_scores": [
                {"dimension": "Technical Skills", "score": 9.0, "evidence": ["Python/FastAPI in 3 projects", "Redis caching at Flipkart"], "gaps": []},
                {"dimension": "Experience Depth", "score": 8.0, "evidence": ["7 years across 3 companies", "Senior IC for 2 years"], "gaps": ["No team lead experience"]},
                {"dimension": "Domain Relevance", "score": 8.0, "evidence": ["B2B SaaS at Flipkart", "Built compliance-adjacent systems"], "gaps": []},
                {"dimension": "Career Trajectory", "score": 8.0, "evidence": ["Consistent upward progression", "Self-directed promotion"], "gaps": []},
            ],
            "strengths": [
                {"point": "Python/FastAPI expert", "evidence": "FastAPI microservices serving 50M req/day at Flipkart"},
                {"point": "Scale experience", "evidence": "Scaled distributed systems to 50M requests per day"},
                {"point": "Strong trajectory", "evidence": "3 progressive roles with increasing scope in 7 years"},
            ],
            "concerns": [
                {"point": "No team leadership", "evidence": "JD hints at lead track; no formal mentoring evidence", "suggested_question": "Have you mentored junior engineers informally or led any cross-team initiatives?"},
                {"point": "Security/compliance exposure", "evidence": "JD mentions SOC 2/ISO 27001; not mentioned in resume", "suggested_question": "Have you worked on systems requiring compliance certifications like SOC 2?"},
            ],
            "recruiter_summary": "Strong Python/FastAPI engineer with 7 years and proven scale experience (50M req/day at Flipkart). Deep B2B SaaS background across 3 companies with consistent growth. Gap is formal team leadership; recommend phone screen focused on mentoring appetite and compliance exposure.",
            "suggested_questions": [
                {"question": "Walk me through how you scaled the Flipkart microservice to 50M req/day.", "addresses": "Technical depth verification"},
                {"question": "Have you worked in systems requiring SOC 2 or ISO 27001 compliance?", "addresses": "Compliance domain knowledge"},
            ],
        },
        "ai_authorship_signal": "none",
        "contradiction_flags": [],
    },
    {
        "filename": "rahul_kumar_backend_dev.pdf",
        "extracted_fields": {
            "full_name": {"value": "Rahul Kumar", "evidence": "Rahul Kumar, Software Engineer", "confidence": "high"},
            "email": {"value": "rahul.k@email.com", "evidence": "rahul.k@email.com", "confidence": "high"},
            "current_title": {"value": "Software Engineer II", "evidence": "Software Engineer II — Swiggy", "confidence": "high"},
            "total_experience_years": {"value": 5, "evidence": "5 years professional experience", "confidence": "medium"},
            "skills": {"value": ["Python", "Django", "PostgreSQL", "AWS", "Docker"], "evidence": "Python, Django, PostgreSQL in Skills", "confidence": "high"},
            "education": {"value": "B.E. Computer Engineering, VIT Vellore, 2019", "evidence": "B.E. CE, VIT (2019)", "confidence": "high"},
            "summary": {"value": "5 years Python developer, Django REST APIs, AWS deployments", "evidence": "5 years building Django APIs on AWS", "confidence": "medium"},
        },
        "score": {
            "overall_score": 7.4,
            "recommendation": "recommend",
            "confidence": "high",
            "dimensional_scores": [
                {"dimension": "Technical Skills", "score": 7.5, "evidence": ["Python/Django confirmed", "AWS deployments mentioned"], "gaps": ["FastAPI not present; uses Django", "No Redis or Kubernetes"]},
                {"dimension": "Experience Depth", "score": 7.0, "evidence": ["5 years across 2 companies", "IC growth visible"], "gaps": ["No senior IC title yet"]},
                {"dimension": "Domain Relevance", "score": 8.0, "evidence": ["Food-tech SaaS background maps well to B2B", "REST API expertise matches JD"], "gaps": []},
                {"dimension": "Career Trajectory", "score": 7.0, "evidence": ["Engineer I → II progression at Swiggy"], "gaps": ["Growth rate slightly slower than typical"]},
            ],
            "strengths": [
                {"point": "Solid Python/Django", "evidence": "5 years Python, Django REST APIs in production at Swiggy"},
                {"point": "AWS proficiency", "evidence": "AWS deployments and cloud infrastructure mentioned across 2 roles"},
                {"point": "API design", "evidence": "Built 12+ REST endpoints handling 2M daily requests"},
            ],
            "concerns": [
                {"point": "FastAPI gap", "evidence": "JD prefers FastAPI; candidate uses Django only", "suggested_question": "Have you worked with FastAPI or are you comfortable picking it up quickly?"},
                {"point": "No Kubernetes", "evidence": "JD lists Kubernetes; Docker present but K8s absent", "suggested_question": "What is your experience with container orchestration beyond Docker Compose?"},
            ],
            "recruiter_summary": "Solid Python/Django engineer with 5 years and proven API development experience at Swiggy. Strong AWS background. Gap is FastAPI (uses Django) and Kubernetes. At 7.4, a strong candidate worth a screen — will need to assess FastAPI comfort and K8s learning appetite.",
            "suggested_questions": [
                {"question": "How quickly have you picked up new frameworks in the past?", "addresses": "FastAPI adoption potential"},
                {"question": "Describe your experience with container orchestration.", "addresses": "Kubernetes gap"},
            ],
        },
        "ai_authorship_signal": "none",
        "contradiction_flags": [],
    },
    {
        "filename": "ananya_iyer_fullstack.pdf",
        "extracted_fields": {
            "full_name": {"value": "Ananya Iyer", "evidence": "Ananya Iyer — Full Stack Developer", "confidence": "high"},
            "email": {"value": "ananya.iyer@email.com", "evidence": "ananya.iyer@email.com", "confidence": "high"},
            "current_title": {"value": "Full Stack Developer", "evidence": "Full Stack Developer — Startup XYZ", "confidence": "high"},
            "total_experience_years": {"value": 4, "evidence": "4 years building web applications", "confidence": "medium"},
            "skills": {"value": ["JavaScript", "React", "Node.js", "Python", "MySQL"], "evidence": "JS, React, Node.js, Python in Skills", "confidence": "high"},
            "education": {"value": "B.Sc. Information Technology, Mumbai University, 2020", "evidence": "B.Sc. IT, Mumbai University (2020)", "confidence": "high"},
            "summary": {"value": "Full stack developer with React and Node.js focus, some Python scripting", "evidence": "4 years full stack development", "confidence": "medium"},
        },
        "score": {
            "overall_score": 5.5,
            "recommendation": "maybe",
            "confidence": "medium",
            "dimensional_scores": [
                {"dimension": "Technical Skills", "score": 5.0, "evidence": ["Python present but not primary language", "No FastAPI/Django experience"], "gaps": ["Backend is Node.js not Python", "No PostgreSQL", "No cloud certifications"]},
                {"dimension": "Experience Depth", "score": 6.0, "evidence": ["4 years total experience", "Full product ownership at startup"], "gaps": ["Full stack not focused enough for senior backend role"]},
                {"dimension": "Domain Relevance", "score": 5.5, "evidence": ["SaaS product background"], "gaps": ["Frontend-heavy background for a backend role"]},
                {"dimension": "Career Trajectory", "score": 5.5, "evidence": ["Progressive responsibility at startup"], "gaps": ["No major tech company experience"]},
            ],
            "strengths": [
                {"point": "Full product ownership", "evidence": "Led end-to-end development at startup with full ownership"},
                {"point": "Python exposure", "evidence": "Python appears in skills and scripting context"},
                {"point": "SaaS background", "evidence": "4 years building SaaS products from scratch"},
            ],
            "concerns": [
                {"point": "Frontend-heavy background", "evidence": "Primary skills are React/Node.js, not Python backend", "suggested_question": "How much of your day-to-day is backend Python vs React/Node?"},
                {"point": "No PostgreSQL or cloud infra", "evidence": "MySQL and no cloud platform experience evident", "suggested_question": "Have you worked with PostgreSQL or managed cloud infrastructure (AWS/GCP)?"},
            ],
            "recruiter_summary": "Full stack developer with 4 years and strong product ownership, but primarily frontend (React/Node.js) rather than Python backend. Python is secondary. Would need significant ramp on FastAPI, PostgreSQL, and cloud infra. Consider only if growth potential for a backend pivot is the criteria.",
            "suggested_questions": [
                {"question": "What percentage of your work is backend Python development?", "addresses": "Backend depth assessment"},
                {"question": "Are you open to transitioning from full stack to backend-focused work?", "addresses": "Role fit alignment"},
            ],
        },
        "ai_authorship_signal": "weak",
        "contradiction_flags": [],
    },
    {
        "filename": "deepak_nair_senior_engineer.pdf",
        "extracted_fields": {
            "full_name": {"value": "Deepak Nair", "evidence": "Deepak Nair — Engineering Lead", "confidence": "high"},
            "email": {"value": "deepak.nair@email.com", "evidence": "deepak.nair@email.com", "confidence": "high"},
            "current_title": {"value": "Engineering Lead", "evidence": "Engineering Lead — Razorpay", "confidence": "high"},
            "total_experience_years": {"value": 9, "evidence": "9 years in software engineering", "confidence": "high"},
            "skills": {"value": ["Python", "FastAPI", "PostgreSQL", "Redis", "Kubernetes", "AWS", "Terraform", "Security"], "evidence": "Python, FastAPI, PostgreSQL, Redis, K8s, AWS, Terraform", "confidence": "high"},
            "education": {"value": "B.Tech CS, NIT Trichy, 2015", "evidence": "B.Tech CS, NIT Trichy, 2015", "confidence": "high"},
            "summary": {"value": "9 years engineering, led team of 8, built payment compliance systems at Razorpay", "evidence": "led team of 8 engineers at Razorpay on PCI-DSS compliant payment platform", "confidence": "high"},
        },
        "score": {
            "overall_score": 9.1,
            "recommendation": "strongly_recommend",
            "confidence": "high",
            "dimensional_scores": [
                {"dimension": "Technical Skills", "score": 9.5, "evidence": ["Python/FastAPI confirmed across 3 roles", "K8s + Terraform production experience"], "gaps": []},
                {"dimension": "Experience Depth", "score": 9.0, "evidence": ["9 years, 4 companies", "Led team of 8 engineers"], "gaps": []},
                {"dimension": "Domain Relevance", "score": 9.5, "evidence": ["PCI-DSS compliance at Razorpay maps directly to SOC2/ISO27001", "Fintech/compliance domain expert"], "gaps": []},
                {"dimension": "Career Trajectory", "score": 8.5, "evidence": ["Engineer → Lead in 9 years", "Progressive scope at each company"], "gaps": []},
            ],
            "strengths": [
                {"point": "Compliance domain expert", "evidence": "Built PCI-DSS compliant payment platform at Razorpay — directly relevant"},
                {"point": "Team leadership", "evidence": "Led team of 8 engineers; JD mentions mentoring"},
                {"point": "Full stack expertise", "evidence": "Python/FastAPI, PostgreSQL, Redis, K8s, Terraform — every required skill present"},
            ],
            "concerns": [
                {"point": "Potential overqualification", "evidence": "9 years + team lead experience; JD is for senior IC, not lead", "suggested_question": "Are you looking for an IC role or is team leadership part of your expectation?"},
            ],
            "recruiter_summary": "Exceptional match. 9 years Python/FastAPI engineering with PCI-DSS compliance experience at Razorpay maps directly to Sprinto's compliance automation focus. Led a team of 8, owns the full infra stack (K8s, Terraform, AWS). Only watch: possible overqualification for a non-lead Senior role — clarify expectations upfront.",
            "suggested_questions": [
                {"question": "What aspects of the role excite you most — IC technical work or building the team?", "addresses": "Overqualification / expectation alignment"},
                {"question": "How did you handle compliance requirements at Razorpay (PCI-DSS)?", "addresses": "Compliance domain depth"},
            ],
        },
        "ai_authorship_signal": "none",
        "contradiction_flags": [],
    },
    {
        "filename": "sneha_gupta_junior_dev.pdf",
        "extracted_fields": {
            "full_name": {"value": "Sneha Gupta", "evidence": "Sneha Gupta — Software Developer", "confidence": "high"},
            "email": {"value": "sneha.gupta@email.com", "evidence": "sneha.gupta@email.com", "confidence": "high"},
            "current_title": {"value": "Software Developer", "evidence": "Software Developer — TCS", "confidence": "high"},
            "total_experience_years": {"value": 2, "evidence": "2 years at TCS", "confidence": "medium"},
            "skills": {"value": ["Python", "Django", "MySQL", "REST APIs"], "evidence": "Python, Django, REST APIs", "confidence": "medium"},
            "education": {"value": "B.Tech CS, Pune University, 2022", "evidence": "B.Tech CS, Pune (2022)", "confidence": "high"},
            "summary": {"value": "2 years Python developer at TCS, building internal tools", "evidence": "2 years building internal tools", "confidence": "medium"},
        },
        "score": {
            "overall_score": 3.8,
            "recommendation": "do_not_advance",
            "confidence": "high",
            "dimensional_scores": [
                {"dimension": "Technical Skills", "score": 4.0, "evidence": ["Python/Django present"], "gaps": ["No FastAPI", "No cloud platform", "No Redis or K8s", "No production scale experience"]},
                {"dimension": "Experience Depth", "score": 3.5, "evidence": ["2 years total"], "gaps": ["JD requires 5+; 3 year gap", "Internal tools only — no customer-facing systems"]},
                {"dimension": "Domain Relevance", "score": 4.0, "evidence": ["TCS services experience"], "gaps": ["Services company background, not product; no SaaS experience"]},
                {"dimension": "Career Trajectory", "score": 3.5, "evidence": ["Still early career"], "gaps": ["Too early for senior role; would need 3 more years to be competitive"]},
            ],
            "strengths": [
                {"point": "Python foundation", "evidence": "Python and Django present — correct base language"},
                {"point": "Early career potential", "evidence": "2 years experience shows early but clear trajectory"},
            ],
            "concerns": [
                {"point": "Insufficient experience", "evidence": "JD requires 5+ years; candidate has 2", "suggested_question": "N/A — recommend not advancing for this role"},
                {"point": "No production scale", "evidence": "Internal tools only; no customer-facing or high-traffic systems", "suggested_question": "N/A — recommend not advancing for this role"},
            ],
            "recruiter_summary": "Strong Python foundation but 3 years short of the 5+ years required. Internal tools at TCS, no SaaS or production-scale experience. Recommend not advancing for this senior role — consider revisiting in 2-3 years or for a junior track if one opens.",
            "suggested_questions": [],
        },
        "ai_authorship_signal": "moderate",
        "contradiction_flags": [],
    },
]


async def seed():
    """Insert sample role + candidates into the database."""
    async with async_session() as db:
        # Check if already seeded
        existing = await db.execute(select(Role).where(Role.title == "Senior Backend Engineer — Demo"))
        if existing.scalar_one_or_none():
            return  # Already seeded

        # Create role
        role = Role(
            id=uuid.uuid4(),
            title="Senior Backend Engineer — Demo",
            jd_text=SAMPLE_JD.strip(),
            blind_mode=True,
            status="active",
            jd_quality_report={
                "flags": [
                    {"flag": "Vague requirement: 'strong problem-solving skills'", "severity": "info", "suggestion": "Consider replacing with a specific, measurable requirement"},
                ],
                "overall_quality": "good",
                "summary": "Well-structured JD with clear technical requirements. Minor: one vague soft skill.",
            },
            created_at=datetime.now(timezone.utc) - timedelta(days=3),
        )
        db.add(role)
        await db.flush()

        # Create resumes and scores
        for i, candidate in enumerate(CANDIDATES):
            resume_id = uuid.uuid4()
            upload_time = datetime.now(timezone.utc) - timedelta(hours=10 - i * 2)

            resume = Resume(
                id=resume_id,
                role_id=role.id,
                original_filename=candidate["filename"],
                file_hash=f"demo_hash_{i}_{uuid.uuid4().hex[:8]}",
                parsed_text=f"[Demo resume for {candidate['extracted_fields']['full_name']['value']}]",
                parse_report={"confidence": 90, "method": "demo", "sections_found": ["EXPERIENCE", "SKILLS", "EDUCATION"], "warnings": []},
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
                raw_scores={"dimensions": [{"dimension": d["dimension"], "score": d["score"] + 0.3} for d in s["dimensional_scores"]]},
                critique={"critiques": [{"dimension": d["dimension"], "original_score": d["score"] + 0.3, "critique": "Score slightly adjusted after reviewing evidence gaps", "adjusted_score": d["score"]} for d in s["dimensional_scores"]]},
            )
            db.add(score)

        await db.commit()
