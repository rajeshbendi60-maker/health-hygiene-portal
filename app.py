from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

app.secret_key = "healthproject"

# ================= DATABASE =================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hygiene.db'

app.config['UPLOAD_FOLDER'] = 'uploads'

DB = SQLAlchemy(app)

# ================= USER TABLE =================

class User(DB.Model):

    id = DB.Column(DB.Integer, primary_key=True)

    username = DB.Column(DB.String(100), unique=True)

    password = DB.Column(DB.String(100))

    # ===== ROLE SYSTEM =====
    # default = normal user

    role = DB.Column(DB.String(20), default="user")

# ================= COMPLAINT TABLE =================

class Complaint(DB.Model):

    id = DB.Column(DB.Integer, primary_key=True)

    username = DB.Column(DB.String(100))

    issue = DB.Column(DB.String(200))

    description = DB.Column(DB.String(500))

    image = DB.Column(DB.String(200))

    street = DB.Column(DB.String(200))

    village = DB.Column(DB.String(200))

    state = DB.Column(DB.String(100))

    pincode = DB.Column(DB.String(20))

    status = DB.Column(DB.String(20), default="Pending")

# ================= HOME =================

@app.route('/')
def home():

    return render_template('index.html')

# ================= REGISTER =================

@app.route('/register', methods=['GET', 'POST'])
def register():

    error = None

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        existing_user = User.query.filter_by(
            username=username
        ).first()

        # ===== USER EXISTS =====

        if existing_user:

            error = "Username Already Exists"

            return render_template(
                'register.html',
                error=error
            )

        # ===== CREATE NORMAL USER =====

        new_user = User(

            username=username,

            password=password,

            role="user"

        )

        DB.session.add(new_user)

        DB.session.commit()

        return redirect('/login')

    return render_template(
        'register.html',
        error=error
    )

# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():

    error = None

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = User.query.filter_by(

            username=username,

            password=password

        ).first()

        # ===== VALID LOGIN =====

        if user:

            session.clear()

            # ===== ADMIN =====

            if user.role == "admin":

                session['admin'] = user.username

                return redirect('/admin')

            # ===== NORMAL USER =====

            else:

                session['user'] = user.username

                return redirect('/dashboard')

        # ===== INVALID LOGIN =====

        error = "Invalid Username or Password"

    return render_template(
        'login.html',
        error=error
    )

# ================= LOGOUT =================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ================= REPORT =================

@app.route('/report', methods=['GET', 'POST'])
def report():

    if 'user' not in session:

        return redirect('/login')

    if request.method == 'POST':

        issue = request.form['issue']

        description = request.form['description']

        street = request.form['street']

        village = request.form['village']

        state = request.form['state']

        pincode = request.form['pincode']

        image_file = request.files['image']

        filename = secure_filename(
            image_file.filename
        )

        # ===== CREATE UPLOAD FOLDER =====

        if not os.path.exists(
            app.config['UPLOAD_FOLDER']
        ):

            os.makedirs(
                app.config['UPLOAD_FOLDER']
            )

        # ===== SAVE IMAGE =====

        image_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        image_file.save(image_path)

        # ===== SAVE COMPLAINT =====

        new_complaint = Complaint(

            username=session['user'],

            issue=issue,

            description=description,

            image=filename,

            street=street,

            village=village,

            state=state,

            pincode=pincode

        )

        DB.session.add(new_complaint)

        DB.session.commit()

        return redirect('/dashboard')

    return render_template('report.html')

# ================= USER DASHBOARD =================

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:

        return redirect('/login')

    complaints = Complaint.query.filter_by(
        username=session['user']
    ).all()

    return render_template(
        'dashboard.html',
        complaints=complaints
    )

# ================= ADMIN DASHBOARD =================

@app.route('/admin')
def admin():

    if 'admin' not in session:

        return redirect('/login')

    complaints = Complaint.query.all()

    return render_template(
        'admin.html',
        complaints=complaints
    )

# ================= STATUS UPDATE =================

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):

    if 'admin' not in session:

        return redirect('/login')

    complaint = Complaint.query.get(id)

    complaint.status = request.form['status']

    DB.session.commit()

    return redirect('/admin')

# ================= IMAGE DISPLAY =================

@app.route('/uploads/<filename>')
def uploaded_file(filename):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )

# ================= MAIN =================

if __name__ == '__main__':

    with app.app_context():

        DB.create_all()

        # ===== CREATE DEFAULT ADMIN =====

        admin_exists = User.query.filter_by(
            username="admin@gmail.com"
        ).first()

        if not admin_exists:

            admin_user = User(

                username="admin@gmail.com",

                password="admin123",

                role="admin"

            )

            DB.session.add(admin_user)

            DB.session.commit()

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )