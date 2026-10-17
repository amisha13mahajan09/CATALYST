
# CATALYST
### Intelligent Placement Readiness Assessment System

CATALYST is a web-based platform that evaluates students' placement readiness across 13 parameters, including academics, coding, technical skills, projects, aptitude, communication, and professional achievements.

It calculates a weighted readiness score out of 100, identifies skill gaps, provides personalized improvement recommendations, and helps placement coordinators analyze student performance.

## Features

- **Student Dashboard:** View placement readiness scores and assessment results.
- **13-Parameter Assessment:** Evaluate academic, technical, professional, and interpersonal skills.
- **Readiness Classification:** Categorizes students as Ready, Moderately Ready, or Needs Improvement.
- **Skill-Gap Analysis:** Identifies weaknesses using predefined benchmarks.
- **Personalized Recommendations:** Suggests prioritized areas for improvement.
- **Progress Tracking:** Maintains assessment history and tracks improvement.
- **Admin Dashboard:** Provides student statistics, department-wise analytics, and performance insights.

## Assessment Parameters

Academics, Coding Languages, Technical Skills, Coding Platforms, LinkedIn Profile, Research Papers, Internships, Hackathons, Courses and Certificates, Aptitude, Communication Skills, Foreign Languages, and Projects.

## Scoring Methodology

CATALYST calculates the overall readiness score using weighted scores across all 13 categories.

**Formula:**

`Readiness Score = Σ (Normalized Category Score × Category Weightage)`

| Score | Classification |
|---|---|
| 76–100 | Ready |
| 50–75 | Moderately Ready |
| Below 50 | Needs Improvement |

The system compares student performance against predefined benchmarks to identify skill gaps and generate improvement recommendations.

## Technology Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python
- **Database:** PostgreSQL
- **APIs:** REST APIs
- **Tools:** Visual Studio Code, Git, GitHub

## Database

PostgreSQL stores student profiles, academic records, technical skills, projects, assessment results, skill gaps, and recommendations. Analytical views support progress tracking and administrative reporting.

## Results

The project includes a relational database structure, assessment scoring framework, readiness classifications, sample assessment records, skill-gap storage, and analytical views for student and department-level insights.

## Installation

```bash
git clone https://github.com/amisha13mahajan09/CATALYST.git
cd CATALYST
```

Configure PostgreSQL and install the required dependencies according to the project setup instructions.

## Author

**Amisha Sarwate**

