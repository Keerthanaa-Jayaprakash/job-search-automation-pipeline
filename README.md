# Job Search Automation Pipeline

An automated Python-based job search pipeline that collects recent **Data Analyst** and **Data Engineer** opportunities, filters and ranks them based on job relevance, generates an Excel report, and delivers the report through email.

## Project Overview

This project automates the repetitive process of searching for relevant jobs across preferred locations and experience levels.

The pipeline uses the **Apify Indeed Jobs Scraper** to collect job listings and then applies custom Python-based filtering and scoring logic to identify the most relevant opportunities.

The final results are exported to an Excel report and automatically sent as an email attachment.

## Pipeline

```text
Indeed Job Listings
        ↓
Apify Indeed Jobs Scraper
        ↓
Raw Job Data
        ↓
Role Filtering
        ↓
Location Filtering
        ↓
Experience Evaluation
        ↓
Skill Matching
        ↓
Freshness Scoring
        ↓
Relevance Scoring
        ↓
Duplicate Removal
        ↓
Excel Report Generation
        ↓
Email Delivery
```

## Key Features

* Collects recent job listings using Apify's Indeed Jobs Scraper
* Searches across multiple Data Analyst and Data Engineer role variations
* Filters jobs based on:

  * Job role
  * Location
  * Experience requirements
  * Relevant technical skills
  * Job freshness
* Excludes senior-level positions that do not match the target experience level
* Calculates a relevance score for each job
* Removes duplicate job listings
* Sorts jobs by relevance
* Generates an Excel report containing the matched jobs
* Includes a debugging/diagnostic sheet for monitoring filtering results
* Automatically sends the generated report through Gmail
* Keeps API credentials and email credentials outside the source code using environment variables

## Target Roles

The current search configuration includes roles such as:

* Data Analyst
* Junior Data Analyst
* Associate Data Analyst
* Data Analytics
* BI Analyst
* Reporting Analyst
* Data Engineer
* Junior Data Engineer
* Associate Data Engineer
* ETL Engineer
* ETL Developer
* Data Pipeline Engineer
* Analytics Engineer

## Target Locations

The current configuration focuses on:

* Bengaluru / Bangalore
* Coimbatore
* Remote / Work From Home

## Skills Considered

The relevance scoring considers skills and keywords including:

* SQL
* Python
* Excel
* Power BI
* Tableau
* ETL
* Data Analysis
* Data Analytics
* Data Visualization
* Pandas
* Spark
* PySpark
* Databricks
* PostgreSQL
* MySQL
* AWS
* Azure
* Data Pipelines
* Data Warehousing
* Data Lakes
* Delta Lake
* Lakehouse

## Relevance Scoring

Jobs are evaluated using a rule-based scoring system that considers multiple factors:

| Factor              | Purpose                                                   |
| ------------------- | --------------------------------------------------------- |
| Role Match          | Determines whether the job title matches the target roles |
| Location Match      | Checks whether the job is in a preferred location         |
| Skill Match         | Evaluates relevant technical skills                       |
| Experience          | Prioritizes jobs suitable for the target experience range |
| Freshness           | Gives preference to recently posted jobs                  |
| Duplicate Detection | Prevents repeated job listings                            |

The resulting score is used to rank jobs from the strongest matches to the weakest matches.

## Output

The pipeline generates:

```text
Job_Report.xlsx
```

The Excel report contains the filtered and ranked job opportunities.

A debugging sheet is also generated to provide visibility into the filtering process, including the number of jobs returned and how many remained after each filtering stage.

## Email Automation

After generating the Excel report, the project can automatically send the report as an email attachment using Gmail SMTP.

The following environment variables are used:

```text
APIFY_TOKEN
EMAIL_USER
EMAIL_PASS
TO_EMAIL
```

Credentials are intentionally kept outside the GitHub repository.

**Do not commit API tokens, Gmail passwords, or App Passwords to GitHub.**

## Technologies Used

* **Python**
* **Pandas**
* **Apify**
* **Indeed Jobs Scraper**
* **Excel / XlsxWriter**
* **Gmail SMTP**
* **Git / GitHub**

## Project Structure

```text
job-search-automation-pipeline/
│
├── scraper.py
├── scraperemail.py
├── requirements.txt
├── run_scraper.bat
├── README.md
└── .gitignore
```

### File Description

| File               | Description                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------ |
| `scraper.py`       | Collects, filters, scores, deduplicates, and exports job listings                          |
| `scraperemail.py`  | Handles email delivery of the generated report                                             |
| `requirements.txt` | Python dependencies required by the project                                                |
| `run_scraper.bat`  | Windows script used to run the pipeline                                                    |
| `README.md`        | Project documentation                                                                      |
| `.gitignore`       | Prevents credentials, generated files, logs, and virtual environments from being committed |

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Keerthanaa-Jayaprakash/job-search-automation-pipeline.git
cd job-search-automation-pipeline
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```cmd
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Set the required environment variables:

```text
APIFY_TOKEN=your_apify_token
EMAIL_USER=your_gmail_address
EMAIL_PASS=your_gmail_app_password
TO_EMAIL=recipient_email
```

For Gmail, an **App Password** should be used instead of the normal Gmail account password.

### 5. Run the pipeline

```bash
python scraper.py
```

The generated Excel report can then be sent through the email automation script.

For Windows, the included batch file can also be used:

```cmd
run_scraper.bat
```

## Future Improvements

Potential improvements include:

* Adding additional job platforms
* Improving job-title classification
* Adding more advanced experience extraction
* Adding configurable search parameters
* Adding a database for historical job tracking
* Tracking jobs that have already been applied to
* Adding application status tracking
* Adding automated scheduling
* Improving relevance scoring with more advanced NLP techniques
* Adding dashboards for job-search analytics

## Disclaimer

This project is intended for personal job-search automation and learning purposes. Job availability and job-site data may change over time.
