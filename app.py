from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "civicconnect_secret"

DATA_FILE = "data/complaints.csv"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ---------- CREATE DATA FILE SAFELY ----------
if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=[
        "id", "description", "location", "category", "priority", "status"
    ])
    df.to_csv(DATA_FILE, index=False)

# ---------- AI LOGIC ----------
def ai_classify(text):
    text = text.lower()
    if "road" in text:
        return "Road", "High"
    elif "water" in text:
        return "Water", "Medium"
    elif "electric" in text or "power" in text:
        return "Electricity", "High"
    elif "garbage" in text or "waste" in text:
        return "Sanitation", "Low"
    else:
        return "General", "Low"

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("home.html")

# ---------- RAISE COMPLAINT ----------
@app.route("/raise", methods=["GET", "POST"])
def raise_complaint():
    if request.method == "POST":
        location = request.form["location"]
        desc = request.form["description"]

        category, priority = ai_classify(desc)
        df = pd.read_csv(DATA_FILE)

        new_id = 1 if df.empty else int(df["id"].max()) + 1

        df.loc[len(df)] = [
            new_id, desc, location, category, priority, "Pending"
        ]
        df.to_csv(DATA_FILE, index=False)

        return render_template(
            "success.html",
            cid=new_id,
            category=category,
            priority=priority
        )

    return render_template("raise.html")

# ---------- TRACK STATUS ----------
@app.route("/track", methods=["GET", "POST"])
def track():
    status = None
    cid = None

    if request.method == "POST":
        cid = request.form["complaint_id"]
        df = pd.read_csv(DATA_FILE)

        row = df[df["id"].astype(str) == cid]
        if not row.empty:
            status = row.iloc[0]["status"]
        else:
            status = "Invalid Complaint ID"

    return render_template("track.html", status=status, cid=cid)

# ---------- ADMIN LOGIN ----------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            error = "Invalid credentials"
    return render_template("admin_login.html", error=error)

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    df = pd.read_csv(DATA_FILE)
    return render_template("admin.html", data=df.to_dict(orient="records"))

# ---------- RESOLVE ----------
@app.route("/resolve/<int:cid>")
def resolve(cid):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    df = pd.read_csv(DATA_FILE)
    df.loc[df["id"] == cid, "status"] = "Resolved"
    df.to_csv(DATA_FILE, index=False)
    return redirect(url_for("admin"))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

# ---------- RUN ----------
if __name__ == "__main__":
    app.run()

