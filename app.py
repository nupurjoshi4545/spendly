from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from werkzeug.security import check_password_hash
from datetime import date, timedelta
from database.db import (
    get_db, init_db, seed_db, create_user, get_user_by_email, get_user_by_id as _db_get_user
)
from database.queries import (
    get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown
)

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'


@app.context_processor
def inject_user():
    user = None
    if session.get("user_id"):
        user = _db_get_user(session["user_id"])
    return {'current_user': user}


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name or not email or not password or not confirm_password:
        flash("All fields are required.")
        return render_template("register.html")
    if "@" not in email:
        flash("Enter a valid email address.")
        return render_template("register.html")
    if password != confirm_password:
        flash("Passwords do not match.")
        return render_template("register.html")
    if len(password) < 6:
        flash("Password must be at least 6 characters.")
        return render_template("register.html")

    user_id = create_user(name, email, password)
    if user_id is None:
        flash("Email already registered.")
        return render_template("register.html")

    flash("Account created successfully! Please log in.")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.")
        return render_template("login.html")

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user = get_user_by_id(session["user_id"])
    if user is None:
        abort(404)

    def parse_date(val):
        if not val:
            return None
        try:
            from datetime import datetime
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            return None

    date_from = parse_date(request.args.get("date_from", "").strip())
    date_to = parse_date(request.args.get("date_to", "").strip())

    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.")
        date_from = date_to = None

    today = date.today()
    this_month_start = today.replace(day=1).isoformat()
    last_3_start = (today - timedelta(days=90)).isoformat()
    last_6_start = (today - timedelta(days=180)).isoformat()
    today_str = today.isoformat()

    # Detect active preset
    active_preset = None
    if date_from is None and date_to is None:
        active_preset = "all"
    elif date_from == this_month_start and date_to == today_str:
        active_preset = "this_month"
    elif date_from == last_3_start and date_to == today_str:
        active_preset = "last_3"
    elif date_from == last_6_start and date_to == today_str:
        active_preset = "last_6"

    transactions = get_recent_transactions(session["user_id"], date_from=date_from, date_to=date_to)
    stats = get_summary_stats(session["user_id"], date_from=date_from, date_to=date_to)
    categories = get_category_breakdown(session["user_id"], date_from=date_from, date_to=date_to)

    return render_template(
        "profile.html",
        user=user,
        expenses=transactions,
        stats=stats,
        categories=categories,
        date_from=date_from or "",
        date_to=date_to or "",
        active_preset=active_preset,
        this_month_start=this_month_start,
        last_3_start=last_3_start,
        last_6_start=last_6_start,
        today_str=today_str,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
