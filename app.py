from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from ai_service import generate_remark

app = Flask(__name__)
app.secret_key = "caresense-secret-key-2026"

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Model
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), nullable=False)

    glucose = db.Column(db.Float, nullable=False)
    hemoglobin = db.Column(db.Float, nullable=False)
    cholesterol = db.Column(db.Float, nullable=False)

    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ───────── ROUTES ─────────

@app.route("/")
def home():
    """Landing page with Add Patient and Check Patient cards."""
    return render_template("home.html", active_page="home")


@app.route("/add", methods=["GET", "POST"])
def add_patient():
    """Form to add a new patient. On POST, saves patient and shows detail with remark."""
    if request.method == "POST":
        name = request.form["name"]
        dob = datetime.strptime(request.form["dob"], "%Y-%m-%d").date()

        if dob > date.today():
            flash("Date of birth cannot be in the future.", "error")
            return redirect(url_for("add_patient"))

        email = request.form["email"]

        glucose = float(request.form["glucose"])
        hemoglobin = float(request.form["hemoglobin"])
        cholesterol = float(request.form["cholesterol"])

        # Generate AI remark via Ollama
        remark = generate_remark(glucose, hemoglobin, cholesterol)

        patient = Patient(
            name=name,
            dob=dob,
            email=email,
            glucose=glucose,
            hemoglobin=hemoglobin,
            cholesterol=cholesterol,
            remarks=remark
        )

        db.session.add(patient)
        db.session.commit()

        flash("Patient record created successfully!", "success")
        return redirect(url_for("patient_detail", patient_id=patient.id))

    return render_template("add_patient.html", active_page="home")


@app.route("/check", methods=["GET", "POST"])
def check_patient():
    """Search for patient by name and DOB."""
    if request.method == "POST":
        name = request.form["name"].strip()
        dob = datetime.strptime(request.form["dob"], "%Y-%m-%d").date()

        if dob > date.today():
            flash("Date of birth cannot be in the future.", "error")
            return redirect(url_for("check_patient"))

        # Case-insensitive name match + exact DOB match
        patient = Patient.query.filter(
            db.func.lower(Patient.name) == name.lower(),
            Patient.dob == dob
        ).first()

        if patient:
            return redirect(url_for("patient_detail", patient_id=patient.id))
        else:
            flash("No patient record found matching that name and date of birth.", "error")
            return render_template("check_patient.html", active_page="home", not_found=True)

    return render_template("check_patient.html", active_page="home", not_found=False)


@app.route("/patient/<int:patient_id>")
def patient_detail(patient_id):
    """Display full patient details with Ollama remark."""
    patient = Patient.query.get_or_404(patient_id)
    return render_template("patient_detail.html", patient=patient, active_page="database")


@app.route("/edit/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    """Edit an existing patient record."""
    patient = Patient.query.get_or_404(patient_id)

    if request.method == "POST":
        patient.name = request.form["name"]
        
        new_dob = datetime.strptime(request.form["dob"], "%Y-%m-%d").date()
        if new_dob > date.today():
            flash("Date of birth cannot be in the future.", "error")
            return redirect(url_for("edit_patient", patient_id=patient.id))
            
        patient.dob = new_dob
        patient.email = request.form["email"]

        patient.glucose = float(request.form["glucose"])
        patient.hemoglobin = float(request.form["hemoglobin"])
        patient.cholesterol = float(request.form["cholesterol"])

        # Re-generate AI remark with updated values
        patient.remarks = generate_remark(
            patient.glucose,
            patient.hemoglobin,
            patient.cholesterol
        )

        db.session.commit()

        flash("Patient record updated successfully!", "success")
        return redirect(url_for("patient_detail", patient_id=patient.id))

    return render_template("edit_patient.html", patient=patient, active_page="database")


@app.route("/delete/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    """Delete a patient record."""
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()

    flash("Patient record deleted.", "info")
    return redirect(url_for("home"))


@app.route("/database")
def database():
    """Display all patient records in a table."""
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template("patient_database.html", patients=patients, active_page="database")


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)