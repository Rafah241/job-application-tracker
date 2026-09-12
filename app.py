from flask import Flask, render_template, request, redirect
import sqlite3
import logging
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)
app.config["TESTING"] = False

logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

ALLOWED_STATUSES = {
    "Applied",
    "Assessment",
    "Interview",
    "Selected",
    "Rejected"
}


def validate_application(company, role, date_applied, status, job_link):
    errors = []

    if not company.strip():
        errors.append("Company name is required.")

    if not role.strip():
        errors.append("Job role is required.")

    if not date_applied:
        errors.append("Application date is required.")
    else:
        try:
            datetime.strptime(date_applied, "%Y-%m-%d")
        except ValueError:
            errors.append("Application date must be valid.")

    if status not in ALLOWED_STATUSES:
        errors.append("Invalid application status.")

    if job_link:
        parsed_url = urlparse(job_link)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            errors.append("Job link must be a valid URL.")

    return errors


def get_db_connection():
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            date_applied TEXT,
            status TEXT,
            job_link TEXT,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()

@app.route("/")
def home():
    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")
    sort_order = request.args.get("sort", "newest")

    conn = get_db_connection()

    query = "SELECT * FROM applications WHERE 1=1"
    params = []

    if search:
        query += " AND (company LIKE ? OR role LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    if sort_order == "oldest":
        query += " ORDER BY date_applied ASC, id ASC"

    elif sort_order == "company_asc":
        query += " ORDER BY company ASC"

    elif sort_order == "company_desc":
        query += " ORDER BY company DESC"

    else:
        query += " ORDER BY date_applied DESC, id DESC"

    applications = conn.execute(
        query,
        params
    ).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]

    applied = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Applied'"
    ).fetchone()[0]

    assessment = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Assessment'"
    ).fetchone()[0]

    interviews = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Interview'"
    ).fetchone()[0]

    selected = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Selected'"
    ).fetchone()[0]

    rejected = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Rejected'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        applications=applications,
        total=total,
        applied=applied,
        assessment=assessment,
        interviews=interviews,
        selected=selected,
        rejected=rejected,
        search=search,
        status_filter=status_filter,
        sort_order=sort_order
    )

@app.route("/add", methods=["POST"])
def add_application():
    company = request.form.get("company", "").strip()
    role = request.form.get("role", "").strip()
    date_applied = request.form.get("date_applied", "").strip()
    status = request.form.get("status", "").strip()
    job_link = request.form.get("job_link", "").strip()
    notes = request.form.get("notes", "").strip()

    errors = validate_application(
        company,
        role,
        date_applied,
        status,
        job_link
    )

    if errors:
        for error in errors:
            flash(error)
        return redirect("/")

    try:
        conn = get_db_connection()

        conn.execute("""
            INSERT INTO applications
            (company, role, date_applied, status, job_link, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company, role, date_applied, status, job_link, notes))

        conn.commit()
        conn.close()

        logger.info(
            f"Application added: company={company}, role={role}"
        )

    except sqlite3.Error as e:
        logger.error(f"Database error while adding application: {e}")
        flash("Unable to save application. Please try again.")

    return redirect("/")


@app.route("/delete/<int:job_id>", methods=["POST"])
def delete_application(job_id):
    try:
        conn = get_db_connection()

        conn.execute(
            "DELETE FROM applications WHERE id = ?",
            (job_id,)
        )

        conn.commit()
        conn.close()

        logger.info(f"Application deleted: id={job_id}")

    except sqlite3.Error as e:
        logger.error(
            f"Database error while deleting application id={job_id}: {e}"
        )
        flash("Unable to delete application. Please try again.")

    return redirect("/")


@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
def edit_application(job_id):

    conn = get_db_connection()

    if request.method == "POST":

        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()
        date_applied = request.form.get("date_applied", "").strip()
        status = request.form.get("status", "").strip()
        job_link = request.form.get("job_link", "").strip()
        notes = request.form.get("notes", "").strip()

        errors = validate_application(
            company,
            role,
            date_applied,
            status,
            job_link
        )

        if errors:
            conn.close()

            for error in errors:
                flash(error)

            return redirect(f"/edit/{job_id}")

        try:
            conn.execute("""
                UPDATE applications
                SET company = ?,
                    role = ?,
                    date_applied = ?,
                    status = ?,
                    job_link = ?,
                    notes = ?
                WHERE id = ?
            """, (
                company,
                role,
                date_applied,
                status,
                job_link,
                notes,
                job_id
            ))

            conn.commit()
            conn.close()

            logger.info("Application updated: id=%s", job_id)

        except sqlite3.Error as e:
            conn.close()

            logger.error(
                "Database error while updating application id=%s: %s",
                job_id,
                e
            )

            flash("Unable to update application. Please try again.")

        return redirect("/")

    job = conn.execute(
        "SELECT * FROM applications WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    return render_template("edit.html", job=job)

    job = conn.execute(
        "SELECT * FROM applications WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    return render_template("edit.html", job=job)


if __name__ == "__main__":
    create_table()
    app.run(debug=True)