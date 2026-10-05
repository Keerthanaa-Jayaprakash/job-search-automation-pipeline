import os
import re
from datetime import datetime, timezone

import pandas as pd
from apify_client import ApifyClient


# ============================================================
# CONFIGURATION
# ============================================================

ACTOR_ID = "valig/indeed-jobs-scraper"

# More targeted searches = better job coverage
SEARCH_ROLES = [
    # Data Analyst
    "Data Analyst",
    "Junior Data Analyst",
    "Associate Data Analyst",
    "Data Analytics",
    "BI Analyst",
    "Reporting Analyst",

    # Data Engineer
    "Data Engineer",
    "Junior Data Engineer",
    "Associate Data Engineer",
    "ETL Engineer",
    "ETL Developer",
    "Data Pipeline Engineer",
    "Analytics Engineer",
]

TARGET_LOCATIONS = [
    "Bengaluru",
    "Coimbatore",
    "Remote",
]

SKILLS = [
    "SQL",
    "Python",
    "Excel",
    "Power BI",
    "Tableau",
    "ETL",
    "data analysis",
    "data analytics",
    "data visualization",
    "Pandas",
    "Spark",
    "PySpark",
    "Databricks",
    "PostgreSQL",
    "MySQL",
    "AWS",
    "Azure",
    "data pipeline",
    "data warehouse",
    "data lake",
    "Delta Lake",
    "Lakehouse",
]

EXCLUDED_SENIORITY = [
    "senior",
    "sr.",
    "sr ",
    "lead",
    "principal",
    "staff",
    "manager",
    "director",
    "head",
    "architect",
    "vice president",
    "vp ",
    "chief",
]

OUTPUT_FILE = "Job_Report.xlsx"


# ============================================================
# VALID TARGET TITLES
# ============================================================

DATA_ANALYST_TITLES = [
    "data analyst",
    "data analysis",
    "data analytics",
    "analytics analyst",
    "bi analyst",
    "business intelligence analyst",
    "reporting analyst",
    "junior data analyst",
    "associate data analyst",
]

DATA_ENGINEER_TITLES = [
    "data engineer",
    "data engineering",
    "etl engineer",
    "etl developer",
    "data pipeline engineer",
    "analytics engineer",
    "big data engineer",
    "junior data engineer",
    "associate data engineer",
]


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values())

    if isinstance(value, list):
        return " ".join(str(v) for v in value)

    return str(value)


def get_company(item):

    employer = item.get("employer", {})

    if isinstance(employer, dict):
        return (
            employer.get("name")
            or employer.get("companyName")
            or ""
        )

    return clean_text(employer)


def get_location(item):

    location = item.get("location", {})

    if isinstance(location, dict):

        parts = []

        for key in [
            "city",
            "admin1Code",
            "admin1Name",
            "admin2Name",
            "admin3Code",
            "country",
        ]:

            value = location.get(key)

            if value:
                parts.append(str(value))

        return " | ".join(
            dict.fromkeys(parts)
        )

    return clean_text(location)


def get_description(item):

    description = item.get(
        "description",
        ""
    )

    if isinstance(description, dict):

        return clean_text(
            description.get("text")
            or description.get("html")
            or description
        )

    return clean_text(description)


def get_date(item):

    return (
        item.get("datePublished")
        or item.get("dateOnIndeed")
        or item.get("datePosted")
        or ""
    )


# ============================================================
# SENIORITY FILTER
# ============================================================

def has_excluded_seniority(title):

    title_lower = clean_text(
        title
    ).lower()

    for term in EXCLUDED_SENIORITY:

        if term in title_lower:
            return True

    return False


# ============================================================
# ROLE MATCHING
# ============================================================

def get_role(title):

    """
    Match ONLY from the job title.

    This prevents unrelated jobs such as:
        AI Engineer
        Software Engineer
        Tax Analyst
        Financial Analyst
        Digital Software Engineering Analyst

    from becoming Data Analyst/Data Engineer.
    """

    title_lower = clean_text(
        title
    ).lower().strip()

    # Data Analyst
    for term in DATA_ANALYST_TITLES:

        if term in title_lower:
            return "Data Analyst"

    # Data Engineer
    for term in DATA_ENGINEER_TITLES:

        if term in title_lower:
            return "Data Engineer"

    return None


# ============================================================
# LOCATION MATCHING
# ============================================================

def get_target_location(location):

    location_lower = clean_text(
        location
    ).lower()

    # Bengaluru
    if any(
        x in location_lower
        for x in [
            "bengaluru",
            "bangalore",
            "blr",
            "karnataka",
            "ka |",
            "| ka",
        ]
    ):
        return "Bengaluru"

    # Coimbatore
    if any(
        x in location_lower
        for x in [
            "coimbatore",
            "cjb",
            "tamil nadu",
            "tn |",
            "| tn",
        ]
    ):
        return "Coimbatore"

    # Remote
    if any(
        x in location_lower
        for x in [
            "remote",
            "work from home",
            "wfh",
        ]
    ):
        return "Remote"

    return None


# ============================================================
# EXPERIENCE
# ============================================================

def get_experience_score(
    title,
    description
):

    text = (
        clean_text(title)
        + " "
        + clean_text(description)
    ).lower()

    # --------------------------------------------------------
    # 0-3 years / fresher
    # --------------------------------------------------------

    fresher_terms = [
        "fresher",
        "freshers",
        "entry level",
        "entry-level",
        "0-1 year",
        "0 - 1 year",
        "0 to 1 year",
        "1 year",
        "1-2 years",
        "1 - 2 years",
        "1 to 2 years",
        "2 years",
        "2-3 years",
        "2 - 3 years",
        "2 to 3 years",
        "0-3 years",
        "0 - 3 years",
        "0 to 3 years",
    ]

    if any(
        term in text
        for term in fresher_terms
    ):
        return 30

    # --------------------------------------------------------
    # Experience range
    # --------------------------------------------------------

    range_match = re.search(
        r"(\d+)\s*(?:-|to)\s*(\d+)\s*years?",
        text
    )

    if range_match:

        low = int(
            range_match.group(1)
        )

        if low <= 3:
            return 30

        if low == 4:
            return 15

        if low == 5:
            return 5

        return 0

    # --------------------------------------------------------
    # X years experience
    # --------------------------------------------------------

    year_match = re.search(
        r"(\d+)\+?\s*years?\s*(?:of)?\s*experience",
        text
    )

    if year_match:

        years = int(
            year_match.group(1)
        )

        if years <= 3:
            return 30

        if years == 4:
            return 15

        if years == 5:
            return 5

        return 0

    # Experience not mentioned
    return 20


# ============================================================
# SKILLS
# ============================================================

def get_skills(item):

    description = get_description(
        item
    ).lower()

    attributes = clean_text(
        item.get(
            "attributes",
            ""
        )
    ).lower()

    employer_attributes = clean_text(
        item.get(
            "employerAttributes",
            ""
        )
    ).lower()

    combined_text = (
        description
        + " "
        + attributes
        + " "
        + employer_attributes
    )

    matched = []

    for skill in SKILLS:

        if skill.lower() in combined_text:

            matched.append(skill)

    return list(
        dict.fromkeys(matched)
    )


# ============================================================
# DATE PARSING
# ============================================================

def parse_date(value):

    if not value:
        return None

    value = str(value)

    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]

    for fmt in formats:

        try:

            dt = datetime.strptime(
                value,
                fmt
            )

            if dt.tzinfo is None:

                dt = dt.replace(
                    tzinfo=timezone.utc
                )

            return dt

        except ValueError:
            pass

    return None


# ============================================================
# FRESHNESS
# ============================================================

def get_freshness_score(
    date_value
):

    dt = parse_date(
        date_value
    )

    if not dt:
        return 0

    now = datetime.now(
        timezone.utc
    )

    age_hours = (
        now - dt
    ).total_seconds() / 3600

    if age_hours <= 24:
        return 10

    if age_hours <= 48:
        return 8

    if age_hours <= 72:
        return 6

    if age_hours <= 7 * 24:
        return 3

    return 0


# ============================================================
# SCORE
# ============================================================

def calculate_score(
    matched_role,
    target_location,
    matched_skills,
    experience_score,
    freshness_score,
):

    score = 0

    # Exact target role
    if matched_role in [
        "Data Analyst",
        "Data Engineer",
    ]:
        score += 40

    # Location
    if target_location in [
        "Bengaluru",
        "Coimbatore",
        "Remote",
    ]:
        score += 20

    # Skills
    score += min(
        15,
        len(matched_skills) * 3
    )

    # Experience
    if experience_score >= 30:
        score += 15

    elif experience_score >= 15:
        score += 10

    elif experience_score >= 5:
        score += 5

    # Freshness
    score += freshness_score

    return min(
        score,
        100
    )


def get_match_label(score):

    if score >= 85:
        return "Excellent Match"

    if score >= 70:
        return "Strong Match"

    if score >= 55:
        return "Good Match"

    if score >= 40:
        return "Possible Match"

    return "Low Match"


# ============================================================
# WHY THIS MATCH?
# ============================================================

def get_match_reason(
    target_role,
    target_location,
    matched_skills,
    experience_score,
    freshness_score,
):

    reasons = []

    reasons.append(
        f"{target_role} title"
    )

    reasons.append(
        target_location
    )

    if matched_skills:

        reasons.append(
            "Skills: "
            + ", ".join(
                matched_skills[:5]
            )
        )

    if experience_score >= 30:

        reasons.append(
            "0-3 years/fresher"
        )

    elif experience_score >= 15:

        reasons.append(
            "Around 4 years"
        )

    elif experience_score >= 5:

        reasons.append(
            "Around 5 years"
        )

    else:

        reasons.append(
            "Experience may be high"
        )

    if freshness_score == 10:

        reasons.append(
            "Posted within 24h"
        )

    elif freshness_score >= 6:

        reasons.append(
            "Recently posted"
        )

    return " + ".join(
        reasons
    )


# ============================================================
# MAIN
# ============================================================

def main():

    token = os.getenv(
        "APIFY_TOKEN"
    )

    if not token:

        print(
            "ERROR: APIFY_TOKEN is not set."
        )

        print(
            "Run: set APIFY_TOKEN=YOUR_TOKEN"
        )

        return

    client = ApifyClient(
        token
    )

    all_jobs = []

    total_returned = 0
    role_matches = 0
    location_matches = 0
    experience_evaluated = 0

    # ========================================================
    # SEARCH ALL TARGETED TERMS
    # ========================================================

    for search_role in SEARCH_ROLES:

        print()
        print(
            "=" * 70
        )

        print(
            f"SEARCHING: {search_role}"
        )

        print(
            "=" * 70
        )

        actor_input = {

            "title": search_role,

            "location": "India",

            "country": "in",

            "limit": 100,

            "datePosted": "1",

            "sort": "date",
        }

        try:

            run = client.actor(
                ACTOR_ID
            ).call(
                run_input=actor_input
            )

            dataset_id = (
                run.default_dataset_id
            )

            items = list(
                client.dataset(
                    dataset_id
                ).iterate_items()
            )

            print(
                f"Indeed returned: {len(items)}"
            )

            total_returned += len(
                items
            )

        except Exception as e:

            print(
                f"ERROR: {e}"
            )

            continue

        # ====================================================
        # PROCESS RESULTS
        # ====================================================

        for item in items:

            title = clean_text(
                item.get("title")
            )

            company = get_company(
                item
            )

            location = get_location(
                item
            )

            description = get_description(
                item
            )

            posted_on = get_date(
                item
            )

            job_url = (
                item.get("jobUrl")
                or item.get("url")
                or ""
            )

            # ------------------------------------------------
            # Title required
            # ------------------------------------------------

            if not title:
                continue

            # ------------------------------------------------
            # Seniority exclusion
            # ------------------------------------------------

            if has_excluded_seniority(
                title
            ):
                continue

            # ------------------------------------------------
            # Strict role matching
            # ------------------------------------------------

            matched_role = get_role(
                title
            )

            if not matched_role:
                continue

            role_matches += 1

            # ------------------------------------------------
            # Location
            # ------------------------------------------------

            target_location = (
                get_target_location(
                    location
                )
            )

            if not target_location:
                continue

            location_matches += 1

            # ------------------------------------------------
            # Experience
            # ------------------------------------------------

            experience_score = (
                get_experience_score(
                    title,
                    description
                )
            )

            experience_evaluated += 1

            # ------------------------------------------------
            # Skills
            # ------------------------------------------------

            matched_skills = get_skills(
                item
            )

            # ------------------------------------------------
            # Freshness
            # ------------------------------------------------

            freshness_score = (
                get_freshness_score(
                    posted_on
                )
            )

            # ------------------------------------------------
            # Score
            # ------------------------------------------------

            score = calculate_score(

                matched_role=
                    matched_role,

                target_location=
                    target_location,

                matched_skills=
                    matched_skills,

                experience_score=
                    experience_score,

                freshness_score=
                    freshness_score,
            )

            # ------------------------------------------------
            # Reason
            # ------------------------------------------------

            reason = get_match_reason(

                target_role=
                    matched_role,

                target_location=
                    target_location,

                matched_skills=
                    matched_skills,

                experience_score=
                    experience_score,

                freshness_score=
                    freshness_score,
            )

            # ------------------------------------------------
            # Store
            # ------------------------------------------------

            all_jobs.append({

                "Platform":
                    "Indeed",

                "Target Role":
                    matched_role,

                "Title":
                    title,

                "Company":
                    company,

                "Posted On":
                    posted_on,

                "Location":
                    target_location,

                "Actual Location":
                    location,

                "Matched Skills":
                    ", ".join(
                        matched_skills
                    ),

                "Experience Score":
                    experience_score,

                "Freshness Score":
                    freshness_score,

                "Match Score":
                    score,

                "Match Level":
                    get_match_label(
                        score
                    ),

                "Why This Match?":
                    reason,

                "Link":
                    job_url,
            })

    # ========================================================
    # DEDUPLICATION
    # ========================================================

    before_dedupe = len(
        all_jobs
    )

    unique_jobs = {}

    for job in all_jobs:

        link = (
            job["Link"]
            .strip()
            .lower()
        )

        if link:

            key = link

        else:

            key = (
                job["Title"]
                .lower()
                .strip()
                + "|"
                + job["Company"]
                .lower()
                .strip()
            )

        if key not in unique_jobs:

            unique_jobs[key] = job

        else:

            if (
                job["Match Score"]
                > unique_jobs[key][
                    "Match Score"
                ]
            ):

                unique_jobs[key] = job

    all_jobs = list(
        unique_jobs.values()
    )

    # ========================================================
    # SORT
    # ========================================================

    all_jobs.sort(

        key=lambda x: (

            x["Match Score"],

            x["Freshness Score"],

            x["Experience Score"],
        ),

        reverse=True,
    )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "FILTER DIAGNOSTICS"
    )

    print(
        "=" * 70
    )

    print(
        f"Search terms:         {len(SEARCH_ROLES)}"
    )

    print(
        f"Indeed returned:       {total_returned}"
    )

    print(
        f"Correct role:          {role_matches}"
    )

    print(
        f"Correct location:      {location_matches}"
    )

    print(
        f"Experience evaluated:  {experience_evaluated}"
    )

    print(
        f"Jobs before dedupe:    {before_dedupe}"
    )

    print(
        f"Unique jobs found:     {len(all_jobs)}"
    )

    # ========================================================
    # DATAFRAME
    # ========================================================

    if all_jobs:

        jobs_df = pd.DataFrame(
            all_jobs
        )

        jobs_df.insert(
            0,
            "S.No",
            range(
                1,
                len(jobs_df) + 1
            )
        )

    else:

        jobs_df = pd.DataFrame(
            columns=[
                "S.No",
                "Platform",
                "Target Role",
                "Title",
                "Company",
                "Posted On",
                "Location",
                "Actual Location",
                "Matched Skills",
                "Experience Score",
                "Freshness Score",
                "Match Score",
                "Match Level",
                "Why This Match?",
                "Link",
            ]
        )

    # ========================================================
    # DEBUG SHEET
    # ========================================================

    debug_df = pd.DataFrame([

        {
            "Metric":
                "Search terms used",

            "Value":
                len(SEARCH_ROLES),
        },

        {
            "Metric":
                "Indeed jobs returned",

            "Value":
                total_returned,
        },

        {
            "Metric":
                "Correct target role",

            "Value":
                role_matches,
        },

        {
            "Metric":
                "Correct target location",

            "Value":
                location_matches,
        },

        {
            "Metric":
                "Experience evaluated",

            "Value":
                experience_evaluated,
        },

        {
            "Metric":
                "Jobs before dedupe",

            "Value":
                before_dedupe,
        },

        {
            "Metric":
                "Final unique jobs",

            "Value":
                len(all_jobs),
        },
    ])

    # ========================================================
    # EXCEL
    # ========================================================

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl"
    ) as writer:

        jobs_df.to_excel(
            writer,
            sheet_name="Jobs",
            index=False
        )

        debug_df.to_excel(
            writer,
            sheet_name="Debug",
            index=False
        )

    # ========================================================
    # TOP JOBS
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "TOP JOBS"
    )

    print(
        "=" * 70
    )

    if not all_jobs:

        print(
            "No matching jobs found."
        )

    else:

        for job in all_jobs[:20]:

            print(

                f'{job["Match Score"]:>3} | '

                f'{job["Match Level"]:<16} | '

                f'{job["Title"]} | '

                f'{job["Company"]} | '

                f'{job["Target Role"]} | '

                f'{job["Location"]}'
            )

    print()

    print(
        "=" * 70
    )

    print(
        f"Excel created: {OUTPUT_FILE}"
    )

    print(
        "=" * 70
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()