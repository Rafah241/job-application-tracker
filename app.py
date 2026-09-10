from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


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

    company = request.form["company"]
    role = request.form["role"]
    date_applied = request.form["date_applied"]
    status = request.form["status"]
    job_link = request.form["job_link"]
    notes = request.form["notes"]

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO applications
        (company, role, date_applied, status, job_link, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        company,
        role,
        date_applied,
        status,
        job_link,
        notes
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/delete/<int:job_id>", methods=["POST"])
def delete_application(job_id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM applications WHERE id = ?",
        (job_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
def edit_application(job_id):

    conn = get_db_connection()

    if request.method == "POST":

        company = request.form["company"]
        role = request.form["role"]
        date_applied = request.form["date_applied"]
        status = request.form["status"]
        job_link = request.form["job_link"]
        notes = request.form["notes"]

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

        return redirect("/")

    job = conn.execute(
        "SELECT * FROM applications WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    return render_template("edit.html", job=job)


if __name__ == "__main__":
    create_table()
    app.run(debug=True)