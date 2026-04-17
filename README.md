# Smart Resume Skill Analyzer & ATS Score Checker
A production-ready Python + Streamlit application that parses PDF resumes, detects role-specific skills, estimates ATS compatibility, and generates actionable recommendations to improve resume quality for target job roles.

## Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [How the ATS Score Works](#how-the-ats-score-works)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Local Setup](#local-setup)
- [How to Use](#how-to-use)
- [Deployment Guide](#deployment-guide)
  - [Deploy on Streamlit Community Cloud](#1-deploy-on-streamlit-community-cloud-recommended)
  - [Deploy with Docker](#2-deploy-with-docker)
- [Configuration & Customization](#configuration--customization)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)

## Project Overview
Recruiters and Applicant Tracking Systems (ATS) scan resumes for keyword relevance, technical skill coverage, and role alignment. This project automates that evaluation pipeline by:
- Extracting text from uploaded PDF resumes
- Detecting required skills with regex-based matching
- Estimating an ATS-style score from 0-100
- Suggesting missing skills and optimization actions
- Visualizing skill frequency and score breakdown

## Key Features
- PDF upload and text extraction using `pdfplumber` with `PyPDF2` fallback
- Skill matching against a predefined technical skill library
- Role-aware analysis (Data Analyst, Data Scientist, BI Analyst, ML Engineer, Frontend Developer)
- Skill frequency count and percentage score
- ATS score with transparent scoring components
- Missing skill recommendations and dynamic suggestions
- Keyword highlighting in extracted resume text
- Interactive charts using Streamlit + Matplotlib

## Tech Stack
- Python
- Streamlit
- Pandas
- Regular Expressions (`re`)
- `pdfplumber`
- `PyPDF2`
- Matplotlib

## How the ATS Score Works
The ATS score is a weighted heuristic score in the range **0-100**:

1. **Skill Coverage Score (60 points)**
   - Proportion of required skills found in resume text.
2. **Resume Length Score (15 points)**
   - Rewards concise but sufficiently detailed resumes.
3. **Keyword Density Score (25 points)**
   - Measures frequency of relevant keywords relative to total words.

Formula:
- `ATS Score = Skill Coverage + Resume Length + Keyword Density`
- Final score is clamped to `0-100`.

## Architecture
The application follows a modular design:

- `resume_reader.py`
  - Handles PDF parsing and text normalization.
- `skill_analyzer.py`
  - Contains skill dictionaries, regex matching, ATS scoring, and suggestions.
- `app.py`
  - Streamlit UI, visualization, and user interaction flow.

## Repository Structure
```text
smart-resume-skill-analyzer-ats-score-checker/
├── app.py
├── resume_reader.py
├── skill_analyzer.py
├── requirements.txt
├── runtime.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── README.md
├── resume_project_description.txt
└── linkedin_project_description.txt
```

## Local Setup
### Prerequisites
- Python 3.11+ recommended
- pip

### Install and Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app will open in your browser. If it does not auto-open, use the local URL shown in the terminal.

## How to Use
1. Launch the app.
2. Select a target job role or keep `General`.
3. (Optional) Add custom keywords (comma-separated).
4. Upload a resume in PDF format.
5. Review:
   - ATS Score (0-100)
   - Detected Skills
   - Missing Skills
   - Skill Frequency and Percentage Score
   - Dynamic Suggestions
   - Keyword highlights in resume text

## Deployment Guide
### 1) Deploy on Streamlit Community Cloud (Recommended)
1. Push this project to a GitHub repository.
2. Log in to Streamlit Community Cloud.
3. Click **New app** and connect your GitHub repository.
4. Set:
   - **Branch**: `main` (or your deployment branch)
   - **Main file path**: `app.py`
5. Ensure `requirements.txt` is in the repository root.
6. Click **Deploy**.
7. After deployment, your app gets a public URL.

Notes:
- Keep sensitive values out of code.
- If you add secrets later, configure them in Streamlit Cloud secrets settings.

### 2) Deploy with Docker
This repository includes a ready-to-use `Dockerfile`.

Build image:
```bash
docker build -t smart-resume-analyzer:latest .
```

Run container:
```bash
docker run --rm -p 8501:8501 smart-resume-analyzer:latest
```

Open:
- `http://localhost:8501`

Deploying this Docker image to cloud platforms (Render, Railway, ECS, Azure Container Apps, etc.) typically requires:
- Exposing port `8501`
- Running command from the Dockerfile
- Keeping the container stateless

## Configuration & Customization
Update skill rules in `skill_analyzer.py`:
- `DEFAULT_SKILL_PATTERNS`: add/remove global skills and regex aliases.
- `ROLE_SKILLS_MAP`: tailor required skill sets by role.

You can also adjust scoring thresholds in:
- `_score_skill_coverage(...)`
- `_score_resume_length(...)`
- `_score_keyword_density(...)`

## Troubleshooting
- **PDF has no extracted text**
  - Try a text-based PDF (not scanned image only).
  - Add OCR preprocessing if needed in future.
- **Module import errors**
  - Reinstall dependencies with `pip install -r requirements.txt`.
- **Port already in use**
  - Run Streamlit on a different port:
    - `streamlit run app.py --server.port 8502`
- **Charts not rendering in container**
  - Ensure Matplotlib is installed from `requirements.txt`.

## Future Improvements
- Upload and parse job descriptions for direct JD-vs-resume matching
- OCR support for scanned resumes
- Section-wise scoring (Summary, Experience, Projects, Skills)
- Exportable PDF/JSON analysis reports
- Batch screening for multiple resumes
