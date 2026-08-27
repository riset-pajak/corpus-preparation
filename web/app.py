"""Web app untuk verifikasi dan editing database corpus perpajakan."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    url_for,
    flash,
)

app = Flask(__name__)
app.secret_key = "corpusprep-secret"  # ganti di production

DB_PATH = Path(__file__).resolve().parent / "data.db"


# --- Database helpers ---

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def require_edit(f):
    """Decorator opsional -- aktifkan env EDITOR_MODE=1 untuk edit terbuka."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


# --- Pages ---

@app.route("/")
def index():
    db = get_db()
    total_reg = db.execute("SELECT COUNT(*) FROM regulations").fetchone()[0]
    total_sec = db.execute("SELECT COUNT(*) FROM sections").fetchone()[0]
    total_top = db.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    by_type = db.execute(
        "SELECT reg_type, COUNT(*) c FROM regulations GROUP BY reg_type ORDER BY c DESC"
    ).fetchall()
    return render_template(
        "index.html",
        total_reg=total_reg,
        total_sec=total_sec,
        total_top=total_top,
        by_type=by_type,
    )


@app.route("/regulations")
def regulations_list():
    db = get_db()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 20
    offset = (page - 1) * per_page

    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    type_filter = request.args.get("type", "")

    where_clauses = []
    params = []

    if q:
        # Coba FTS5 dulu, fallback LIKE
        try:
            rows_fts = db.execute(
                """SELECT r.id FROM regulations r, regulations_fts fts
                   WHERE fts MATCH ? AND r.rowid = fts.rowid""",
                (q,),
            ).fetchall()
            if rows_fts:
                ids = [r["id"] for r in rows_fts]
                placeholders = ",".join("?" * len(ids))
                where_clauses.append(f"r.id IN ({placeholders})")
                params.extend(ids)
        except Exception:
            pass
        if not any("rowid = fts.rowid" in str(w) for w in where_clauses):
            where_clauses.append(
                "(r.title LIKE ? OR r.full_identifier LIKE ?)"
            )
            params.extend([f"%{q}%", f"%{q}%"])

    if status_filter:
        where_clauses.append("r.status = ?")
        params.append(status_filter)
    if type_filter:
        where_clauses.append("r.reg_type = ?")
        params.append(type_filter)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    order = request.args.get("order", "year DESC")
    valid_orders = {"year DESC", "year ASC", "reg_type", "full_identifier", "title"}
    if order not in valid_orders:
        order = "year DESC"

    count = db.execute(
        f"SELECT COUNT(*) FROM regulations r {where_sql}", params
    ).fetchone()[0]

    rows = db.execute(
        f"SELECT r.* FROM regulations r {where_sql} ORDER BY {order} LIMIT ? OFFSET ?",
        [*params, per_page, offset],
    ).fetchall()

    types = db.execute(
        "SELECT DISTINCT reg_type FROM regulations ORDER BY reg_type"
    ).fetchall()
    statuses = db.execute(
        "SELECT DISTINCT status FROM regulations ORDER BY status"
    ).fetchall()

    pages_total = (count + per_page - 1) // per_page

    return render_template(
        "list.html",
        regs=rows,
        page=page,
        pages_total=pages_total,
        total=count,
        q=q,
        status_filter=status_filter,
        type_filter=type_filter,
        types=[t["reg_type"] for t in types],
        statuses=[s["status"] for s in statuses],
    )


@app.route("/regulation/<reg_id>")
def regulation_detail(reg_id):
    db = get_db()
    reg = db.execute("SELECT * FROM regulations WHERE id=?", (reg_id,)).fetchone()
    if not reg:
        flash("Regulasi tidak ditemukan.", "danger")
        return redirect(url_for("regulations_list"))

    sections = db.execute(
        "SELECT * FROM sections WHERE regulation_id=? ORDER BY section_order",
        (reg_id,),
    ).fetchall()

    topics = db.execute(
        "SELECT topic FROM topics WHERE regulation_id=?", (reg_id,)
    ).fetchall()

    return render_template(
        "detail.html", reg=reg, sections=sections, topics=topics
    )


@app.route("/regulation/<reg_id>/edit", methods=["GET", "POST"])
@require_edit
def regulation_edit(reg_id):
    db = get_db()
    reg = db.execute("SELECT * FROM regulations WHERE id=?", (reg_id,)).fetchone()
    if not reg:
        flash("Regulasi tidak ditemukan.", "danger")
        return redirect(url_for("regulations_list"))

    if request.method == "POST":
        data = request.form
        db.execute(
            """UPDATE regulations SET
                title=?, reg_type=?, number=?, year=?,
                status=?, replaced_by=?, source_path=?, source_type=?
               WHERE id=?""",
            (
                data["title"],
                data["reg_type"],
                data["number"],
                int(data["year"]) if data["year"] else None,
                data["status"],
                data["replaced_by"],
                data["source_path"],
                data["source_type"],
                reg_id,
            ),
        )
        db.commit()
        flash("Regulasi berhasil diperbarui.", "success")
        return redirect(url_for("regulation_detail", reg_id=reg_id))

    return render_template("edit.html", reg=reg)


@app.route("/section/<section_id>/edit", methods=["GET", "POST"])
@require_edit
def section_edit(section_id):
    db = get_db()
    sec = db.execute("SELECT * FROM sections WHERE id=?", (section_id,)).fetchone()
    if not sec:
        flash("Section tidak ditemukan.", "danger")
        return redirect(url_for("regulation_detail", reg_id=sec["regulation_id"]))

    reg = db.execute("SELECT full_identifier FROM regulations WHERE id=?", (sec["regulation_id"],)).fetchone()

    if request.method == "POST":
        data = request.form
        db.execute(
            """UPDATE sections SET
                section_number=?, section_title=?, text=?, raw_text=?
               WHERE id=?""",
            (
                data["section_number"],
                data["section_title"],
                data["text"],
                data["raw_text"],
                section_id,
            ),
        )
        db.commit()
        flash("Section berhasil diperbarui.", "success")
        return redirect(url_for("regulation_detail", reg_id=sec["regulation_id"]))

    return render_template("section_edit.html", section=sec, reg_identifier=reg["full_identifier"])


@app.route("/topic/<reg_id>/add", methods=["POST"])
@require_edit
def topic_add(reg_id):
    topic = request.form.get("topic", "").strip()
    if not topic:
        flash("Topik kosong.", "warning")
    else:
        db = get_db()
        existing = db.execute(
            "SELECT 1 FROM topics WHERE regulation_id=? AND topic=?",
            (reg_id, topic),
        ).fetchone()
        if existing:
            flash(f"Topik '{topic}' sudah ada.", "info")
        else:
            db.execute(
                "INSERT INTO topics (regulation_id, topic) VALUES (?, ?)",
                (reg_id, topic),
            )
            db.commit()
            flash(f"Topik '{topic}' ditambahkan.", "success")
    return redirect(url_for("regulation_detail", reg_id=reg_id))


@app.route("/topic/<reg_id>/<topic>/remove", methods=["POST"])
@require_edit
def topic_remove(reg_id, topic):
    db = get_db()
    db.execute(
        "DELETE FROM topics WHERE regulation_id=? AND topic=?",
        (reg_id, topic),
    )
    db.commit()
    flash(f"Topik '{topic}' dihapus.", "success")
    return redirect(url_for("regulation_detail", reg_id=reg_id))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
