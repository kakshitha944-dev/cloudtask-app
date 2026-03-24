# CloudTask — Full CI/CD DevSecOps Project

A Flask task management web application demonstrating a complete
**VS Code → GitHub → CI/CD → EC2 → ZAP** DevSecOps pipeline.

---

## Pipeline Overview

```
VS Code (develop) 
    ↓  git push
GitHub (private repo)
    ↓  triggers
GitHub Actions
    ├── Stage 1: Build + flake8 Lint + Bandit Security Scan
    ├── Stage 2: SonarCloud Code Quality & Security Analysis
    ├── Stage 3: SSH Deploy to AWS EC2 + Gunicorn restart
    └── Stage 4: OWASP ZAP Dynamic Security Scan → report artifact
```

---

## Prerequisites

- AWS EC2 instance (Ubuntu 22.04 LTS, t2.micro or better)
- GitHub account + private repository
- SonarCloud account (free for public/student projects)

---

## Step-by-Step Setup

### Step 1 — Push code to GitHub

```bash
# In VS Code terminal
git init
git remote add origin https://github.com/YOUR_USERNAME/cloudtask.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### Step 2 — Set up SonarCloud

1. Go to https://sonarcloud.io and sign in with GitHub.
2. Click **+** → **Analyze new project** → select your repo.
3. Choose **GitHub Actions** as the analysis method.
4. Copy your **SONAR_TOKEN**.
5. Edit `sonar-project.properties`:
   - Replace `YOUR_GITHUB_USERNAME` with your GitHub username.
   - Replace `YOUR_SONARCLOUD_ORG` with your SonarCloud org name.

### Step 3 — Launch and configure EC2

1. Launch an **Ubuntu 22.04** EC2 instance (t2.micro).
2. Create or use an existing key pair — save the `.pem` file.
3. In **Security Groups**, add inbound rule: **TCP port 5000**, source `0.0.0.0/0`.
4. SSH into the instance and run the setup script:

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
# Upload ec2_setup.sh then run:
bash ec2_setup.sh
```

### Step 4 — Add GitHub Secrets

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name   | Value                                      |
|---------------|--------------------------------------------|
| `EC2_HOST`    | Your EC2 public IP e.g. `18.123.45.67`    |
| `EC2_USER`    | `ubuntu`                                   |
| `EC2_SSH_KEY` | Full contents of your `.pem` private key   |
| `SONAR_TOKEN` | Token from SonarCloud                      |

### Step 5 — Make a change and trigger the pipeline

```bash
# In VS Code — edit any source file, e.g. add a comment to app.py
# Then:
git add .
git commit -m "feat: update task form validation"
git push origin main
```

Watch the pipeline run in **GitHub → Actions tab**.

---

## Local Development

```bash
# Clone and set up
git clone https://github.com/YOUR_USERNAME/cloudtask.git
cd cloudtask
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install flake8 bandit

# Run locally
python app.py
# Visit http://127.0.0.1:5000
```

### Run static analysis locally

```bash
# Lint
flake8 . --max-line-length=100 --exclude=.git,__pycache__,venv

# Security scan
bandit -r . -x ./venv -ll
```

---

## Project Structure

```
cloudtask/
├── app.py                          # Flask application + all routes
├── models.py                       # SQLAlchemy models (User, Task)
├── requirements.txt                # Python dependencies
├── sonar-project.properties        # SonarCloud configuration
├── cloudtask.service               # systemd service for Gunicorn on EC2
├── ec2_setup.sh                    # EC2 first-time setup script
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml                  # Full 4-stage CI/CD pipeline
├── .zap/
│   └── rules.tsv                   # OWASP ZAP suppression rules
└── templates/
    ├── base.html                   # Base layout with Bootstrap 5
    ├── login.html
    ├── register.html
    ├── index.html                  # Task list
    ├── add_task.html
    └── edit_task.html
```

---

## Security Measures Implemented

| Vulnerability | Fix Applied |
|---|---|
| Hardcoded SECRET_KEY | `os.environ.get("SECRET_KEY")` |
| Debug mode in production | `debug=False` + Gunicorn |
| Plain-text error responses | `flash()` messages + redirects |
| No input validation | Server-side length + regex checks |
| User enumeration on login | Generic "Invalid email or password" message |
| Horizontal privilege escalation | Ownership check on edit/delete |
| GET-based delete (CSRF risk) | Changed to POST-only with `<form>` |
| Missing authentication | `@login_required` on all task routes |
