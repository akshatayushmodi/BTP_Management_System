from flask import Flask, request, jsonify, flash, redirect, url_for , render_template, session , make_response
from flask_pymongo import PyMongo, ObjectId
from werkzeug.utils import secure_filename
from gridfs import GridFS
import random
import email, smtplib, ssl, os
from bson import ObjectId
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bson.errors import InvalidId


app = Flask(__name__)

# Your MongoDB connection string
CONNECTION_STRING = "mongodb+srv://Lancer:Hh9Rr7h17GIgSPY1@cluster0.nf6kpbe.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


app.config["MONGO_URI"] = CONNECTION_STRING
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'optional_default')
mongo = PyMongo(app)

db = mongo.cx['btp']
fs = GridFS(db)

# def init_db():
#     try:
#         # Simplified check to list database names
#         print(mongo.cx.list_database_names())
#         print("Connected to MongoDB.")
        
#         # Your existing logic...
        
#     except Exception as e:  # Catching a generic exception for debugging
#         print(f"An error occurred: {e}")
# init_db()



@app.route('/')
def index():
    if session.get('id') and session.get('role') == 'student':
        return redirect('/student_home')
    if session.get('id') and session.get('role') == 'faculty':
        return redirect('/faculty_home')
    if session.get('id') and session.get('role') == 'admin':
        return redirect('/admin_home')
    
    # return render_template("home.html")
    return "Hello World!"

def send_otp_signup(otp ,receiver_email):
    sender_email = "testemailskgp@gmail.com"
    subject = "OTP for Email Verification in BTP Report Management Website"

    body = "Welcome to BTP Report Management System !!!"+ "\nOTP: " + str(otp) + "\nUse this otp for verifying your Institute Email Id.\n\nRegards, \nBTP Report Management System"

    # password = input("Type your password and press enter:")
    password = "rlfm iyro bnpe zexv"

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

# Route for OTP verification
@app.route('/verify_otp_signup', methods=['GET', 'POST'])
def verify_otp_signup():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if 'otp' in session and 'email' in session:
            if entered_otp == str(session['otp']):
                # OTP verification successful
                users_collection = db.users
                new_user = {
                    "id": session['id'],
                    "password": session['password'],
                    "full_name": session['full_name'],
                    "email": session['email'],
                    "department": session['department'],
                    "role": session['role']
                }
                
                # Clear session
                session.pop('otp')
                session.pop('email')
                session.pop('id')
                session.pop('password')
                session.pop('full_name')
                session.pop('department')
                session.pop('role')

                users_collection.insert_one(new_user)

                flash('You have successfully Signed Up!!!', 'success')
                return redirect(url_for('signup'))  # Redirect after POST to prevent resubmissions
            else:
                flash('Incorrect OTP. Please try again.', 'error')
                return redirect('/verify_otp_signup')
        else:
            flash('Session expired. Please try again.', 'error')
            return redirect('/signup')

    return render_template('verify_otp.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users_collection = db.users

        id = request.form.get('id')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        email = request.form.get('email').lower()
        department = request.form.get('department')

        existing_user = users_collection.find_one({"id": id})
        if existing_user:
            flash('Username already exists', 'error')  # Using flash for user feedback
            return redirect(url_for('signup'))
        
        # Check ID length and determine user type/role
        role = None
        if len(id) == 9 and id.isalnum():
            role = 'student'
        elif len(id) == 5 and id.isalnum():
            role = 'faculty'
        else:
            flash('Invalid ID', 'error')
            return redirect(url_for('signup'))
        
        # Check if email is authorized under KGP domain
        # if not email.endswith('iitkgp.ac.in') and not email.endswith('@kgpian.iitkgp.ac.in'):
        #     flash('Your email is not authorized under IITKGP domain. Please use your institute email.', 'error')
        #     return redirect(url_for('signup'))
        

        # Check if email already exists
        existing_email = users_collection.find_one({"email": email})
        if existing_email:
            flash('Email already exists', 'error')
            return redirect(url_for('signup'))

        
        # Generate OTP
        otp = random.randint(100000,999999)
        # Send OTP to the user's email address
        send_otp_signup(otp, email)
        # Store the OTP in session for verification
        session['otp'] = otp
        session['email'] = email
        session['id'] = id
        session['password'] = password
        session['full_name'] = full_name
        session['department'] = department
        session['role'] = role

        flash('An OTP has been sent to your email address.', 'success')
        return redirect('/verify_otp_signup')

    return render_template('signup.html')  # Show the form for GET requestste('templates/signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('id'):
        flash("You are already logged in!")
        return redirect('/')
    if request.method == 'POST':
        id = request.form.get('id')
        password = request.form.get('password')

        users_collection = db.users
        user = users_collection.find_one({"id": id, "password": password})
        if user:
            # Authentication successful, set session
            session['id'] = user['id']
            session['role'] = user.get('role')
            flash('Login successful', 'success')

            rname = user.get('role')
            if rname == 'student':
                # Redirect to student home page
                return redirect('/student_home')
            elif rname== 'faculty':
                # Redirect to faculty home page
                return redirect('/faculty_home')
            elif rname== 'admin':
                # Redirect to admin home page
                return redirect('/admin_home')
        else:
            flash('Invalid ID or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

def send_otp_forgot_password(otp ,receiver_email):
    sender_email = "testemailskgp@gmail.com"
    subject = "OTP for Resetting Password in BTP Report Management Website"

    body = "Welcome to BTP Report Management System !!!" + "\nOTP: " + str(otp) + "\nUse this otp to reset your password.\n\nRegards, \nBTP Report Management System"

    # password = input("Type your password and press enter:")
    password = "rlfm iyro bnpe zexv"

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').lower()

        # Assuming you have a users collection in your MongoDB database
        users_collection = db.users

        # Check if email exists in the database
        user = users_collection.find_one({"email": email})
        if user:
            # Generate OTP
            otp = random.randint(100000, 999999)
            # Send OTP to the user's email address (replace this with your email sending function)
            send_otp_forgot_password(otp,email)  # Assuming send_otp is a function to send OTP
            # Store the OTP and email in session for verification
            session['otp'] = otp
            session['email'] = email

            flash('An OTP has been sent to your email address.', 'success')
            return redirect('/verify_otp_forgot_password')

        else:
            flash('Email address not found.', 'error')
            return redirect('/forgot_password')

    return render_template('forgot_password.html')

# Route for OTP verification
@app.route('/verify_otp_forgot_password', methods=['GET', 'POST'])
def verify_otp_forgot_password():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if 'otp' in session and 'email' in session:
            if entered_otp == str(session['otp']):
                # OTP verification successful
                return redirect('/reset_password')
            else:
                flash('Incorrect OTP. Please try again.', 'error')
                return redirect('/verify_otp_forgot_password')
        else:
            flash('Session expired. Please try again.', 'error')
            return redirect('/forgot_password')

    return render_template('verify_otp.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            # Assuming you have a users collection in your MongoDB database
            users_collection = db.users

            # Update the user's password in the database
            try:
                # Update the password in the database
                users_collection.update_one({"email": session['email']}, {"$set": {"password": password}})
            except Exception as e:
                # Handle exceptions (e.g., database errors)
                print("Error updating password:", e)

            # Clear session
            session.pop('otp')
            session.pop('email')

            flash('Password reset successfully. You can now login with your new password.', 'success')
            return redirect('/login')
        else:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect('/reset_password')

    return render_template('reset_password.html')


@app.route('/student_home')
def student_home():
    if session.get('id') and session.get('role') == 'student':
        # return render_template('student_home.html')
        return "Hey student!!!"
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect('/login')

@app.route('/faculty_home')
def faculty_home():
    if session.get('id') and session.get('role') == 'faculty':
        # return render_template('faculty_home.html')
        return "Hey faculty!!!"
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect('/login')

@app.route('/admin_home')
def admin_home():
    if session.get('id') and session.get('role') == 'admin':
        # return render_template('admin_home.html')
        return "Hey admin!!!"
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect('/login')
    
# Route to view user profile
@app.route('/profile')
def view_profile():
    if 'id' in session:
        user_id = session['id']
        users_collection = db.users
        user = users_collection.find_one({'id': user_id})
        if user:
            # Render the profile template with profile data
            return render_template('profile.html', profile_info=user)
        else:
            flash('User not found', 'error')
            return redirect(url_for('index'))
    else:
        flash('Unauthorized access. Sign In first.', 'error')
        return redirect(url_for('index'))
    
@app.route('/btp_list')
def btp_list():
    if session.get('id') and session.get('role') in ['faculty', 'student']:
        btp_collection = db.btp_list
        users_collection = db.users
        application_collection = db.application

        projects_cursor = btp_collection.find()  # This is a cursor
        projects_list = []  # Create an empty list to hold modified project details

        flag = 1
        for project in projects_cursor:
            # Fetch the professor's details for each project
            user = users_collection.find_one({"id": project['prof_id']})

            # Initialize project status as 'Apply' by default
            project_status = 'Apply'
            application_id = "None"
            # If the user is a student, check their application and approval status for each project
            if session.get('role') == 'student':
                roll_no = session.get('id')
                application = application_collection.find_one({"btp_id": str(project["btp_id"]), "roll_no": roll_no})
                
                if application:
                    application_id = application["_id"]
                    if application["status"] == "Approved":
                        project_status = 'Approved'
                    elif application["status"] == "Pending":
                        project_status = 'Pending'
                    elif application["status"] == "Approved by Guide":
                        project_status = 'Approved by Guide'
                    elif application["status"] == "Applied for Co-Guide":
                        project_status = 'Applied for Co-Guide'
                    elif application["status"] == "Temporarily Confirmed":
                        project_status = 'Temporarily Confirmed'
                    elif application["status"] == "Confirmed":
                        project_status = 'Confirmed'
                        flag=0

            # Append professor details and project status to the project dictionary
            project_with_details = {
                **project,
                'prof_name': user.get('full_name', ''),
                'prof_email': user.get('email', ''),
                'department': user.get('department', ''),
                'status': project_status,  # Include project status
                'application_id': application_id
            }

            # Add this updated project dictionary to the list
            projects_list.append(project_with_details)

        # Pass the list of projects (with professor details and project status) to the template
        return render_template('btp_list.html', projects=projects_list, flag=flag)
    else:
        flash('Please login to view the BTP list', 'error')
        return redirect(url_for('login'))

@app.route('/upload_project', methods=['GET', 'POST'])
def upload_project():
    if session.get('id') and session.get('role') == 'faculty':
        if request.method == 'POST':
            btp_collection = db.btp_list
            
            prof_id = session.get('id')
            btp_name = request.form.get('btp_name')
            
             # Check for an existing project with the same name and professor ID
            existing_project = btp_collection.find_one({"btp_name": btp_name, "prof_id": prof_id})
            if existing_project:
                flash('A project with the same name already exists. Please choose a different name.', 'error')
                return redirect('/upload_project')
            
            while True:
                random_no = random.randint(10000, 99999)
                if not btp_collection.find_one({"btp_id": random_no}):
                    break  # If the generated btp_id is unique, exit the loop 
            
            btp_id = str(random_no)
            
            project_file = request.files['project_file']
            file_id = fs.put(project_file, filename=project_file.filename, content_type=project_file.content_type)

            new_project = {
                "btp_id": btp_id,
                "btp_name" : btp_name,
                "prof_id": prof_id,
                "project_file_id" : file_id
            }
            
            btp_collection.insert_one(new_project)
            flash('Project uploaded successfully', 'success')
            return redirect('/btp_list')
        return render_template('upload_project.html')
    else :
        flash('Please Login before applying', 'error')
        return redirect(url_for('login'))

@app.route('/file/<file_id>')
def file(file_id):
    file = fs.get(ObjectId(file_id))
    response = make_response(file.read())
    response.mimetype = file.content_type
    return response

@app.route('/apply_for_btp', methods=['GET', 'POST'])
def apply_for_btp():
    if session.get('id') and session.get('role') == 'student':
        if request.method == 'POST':
            application_collection = db.application
            btp_id = request.form.get('btp_id')
            roll_no = session.get('id')

            existing_application = application_collection.find_one({"btp_id": btp_id, "roll_no": roll_no})
            if existing_application:
                flash('You have already applied for this project.', 'error')
                return redirect(url_for('btp_list'))
            
            new_application = {
                "btp_id": btp_id,
                "roll_no": roll_no,
                "status" : "Pending",
            }

            application_collection.insert_one(new_application)

            flash('Application submitted successfully', 'success')
            # Make sure to redirect back to 'btp_list' to refresh the list and reflect the change
            return redirect(url_for('btp_list'))
        else:
            # If the request method is not POST, just redirect to 'btp_list'
            return redirect(url_for('btp_list'))
    else:
        flash('Please Login before applying', 'error')
        return redirect(url_for('login'))

    
@app.route('/application_list')
def application_list():
    if session.get('id') and session.get('role') == 'faculty':
        users_collection = db.users
        application_collection = db.application
        prof_id = session.get('id')
        projects = db.btp_list.find({"prof_id": prof_id})

        applications_per_project = {}
        project_name = {}
        # print(prof_id)
        for project in projects:
            applications_cursor = application_collection.find({"btp_id": str(project["btp_id"])})
            applications_list = []
            for application in applications_cursor:
                user = users_collection.find_one({"id": str(application['roll_no'])})
                if user:
                    # Create a new dictionary for the application with all details
                    detailed_application = {
                        "id" : application["_id"],
                        "status" : application['status'],
                        "roll_no": application['roll_no'],
                        "student_name": user.get('full_name', 'Unknown'),
                        "email": user.get('email', 'Unknown'),
                        "department": user.get('department', 'Unknown')
                    }
                    # print(detailed_application)
                    applications_list.append(detailed_application)
            applications_per_project[project["btp_id"]] = applications_list
            project_name[project["btp_id"]] = project["btp_name"]

        return render_template('application_list.html', applications_per_project=applications_per_project ,project_name = project_name)
    else:
        flash('Unauthorized access. Please login as faculty.', 'error')
        return redirect(url_for('login'))
 
 
@app.route('/application_approval/<application_id>', methods=['POST'])
def application_approval(application_id):
    action = request.form.get('action')
    
    # Validate application_id is not None or empty
    if not application_id or not action:
        flash('Missing application ID or action.', 'error')
        return redirect(url_for('application_list'))

    try:
        # Ensure application_id is a valid ObjectId
        valid_application_id = ObjectId(application_id)
    except InvalidId:
        flash('Invalid application ID.', 'error')
        return redirect(url_for('application_list'))

    try:
        application_collection = db.application
        btp_id = application_collection.find_one({"_id": valid_application_id}).get("btp_id")

        btp_collection = db.btp_list
        btp_project = btp_collection.find_one({"btp_id": btp_id})

        if btp_project:
                prof_id = btp_project.get('prof_id')
                professor = db.users.find_one({"id": prof_id})
                professor_department = professor.get('department')
                
                student = db.users.find_one({"id": application_collection.find_one({"_id": valid_application_id})['roll_no']})
                student_department = student.get('department')

                if professor_department == student_department:
                    # Proceed with the database update using valid_application_id
                    result = application_collection.update_one(
                        {"_id": valid_application_id},
                        {"$set": {"status": "Approved" if action == "approve" else "Pending"}}
                    )

                    if result.modified_count == 1:
                        flash('Application updated successfully.', 'success')
                    else:
                        flash('Application could not be updated.', 'error')
                else:
                    return redirect(url_for('select_co_guides',application_id=valid_application_id))

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')

    return redirect(url_for('application_list')) 

@app.route('/approved_list')
def approved_list():
    if session.get('id') and session.get('role') == 'faculty':
        users_collection = db.users
        application_collection = db.application
        prof_id = session.get('id')
        projects = db.btp_list.find({"prof_id": prof_id})

        approved_per_project = {}
        project_name = {}

        # print(prof_id)
        for project in projects:
            applications_cursor = application_collection.find({"btp_id": str(project["btp_id"]), "status" : "Approved"})
            applications_list = []
            for application in applications_cursor:
                user = users_collection.find_one({"id": str(application['roll_no'])})
                if user:
                    # Create a new dictionary for the application with all details
                    detailed_application = {
                        "id" : application["_id"],
                        "roll_no": application['roll_no'],
                        "student_name": user.get('full_name', 'Unknown'),
                        "email": user.get('email', 'Unknown'),
                        "department": user.get('department', 'Unknown')
                    }
                    # print(detailed_application)
                    applications_list.append(detailed_application)
            approved_per_project[project["btp_id"]] = applications_list
            project_name[project["btp_id"]] = project["btp_name"]

        return render_template('approved_list.html', approved_per_project=approved_per_project,project_name = project_name )
    else:
        flash('Unauthorized access. Please login as faculty.', 'error')
        return redirect(url_for('login'))

@app.route('/change_application_status/<application_id>', methods=['POST'])
def change_application_status(application_id):
    if session.get('role') != 'faculty':
        flash('Unauthorized access. Please login as faculty.', 'error')
        return redirect(url_for('login'))

    action = request.form.get('action')
    if action == 'reject':
        # Assuming you have a function to update the application status, or you can directly update here
        db.application.update_one({'_id': ObjectId(application_id)}, {'$set': {'status': 'Pending'}})
        
        co_guides_selected = db.co_guides_selected.find_one({"application_id": ObjectId(application_id)})
        if co_guides_selected:
            db.co_guides_selected.delete_many({"application_id": ObjectId(application_id)})
            
        flash('Application status changed to Pending.', 'success')
    else:
        flash('Invalid action.', 'error')

    return redirect(url_for('approved_list'))


@app.route('/list_and_delete_applications')
def list_and_delete_applications():
    if session.get('id') and session.get('role') == 'student':
        users_collection = db.users
        application_collection = db.application
        btp_collection = db.btp_list
        user_roll_no = session.get('id')
        user_applications = application_collection.find({"roll_no": user_roll_no})
        
        applications = []
        for application in user_applications:
            btp = btp_collection.find_one({"btp_id": application["btp_id"]})
            prof_id = btp["prof_id"]
            prof = users_collection.find_one({"id": prof_id})
            application["btp_name"] = btp["btp_name"]
            application["prof_name"] = prof["full_name"]
            application["department"] = prof["department"]
            application["email"] = prof["email"]
            applications.append(application)
        
        return render_template('list_and_delete_applications.html', applications=applications)
    else:
        flash('Please login as a student to view your applications.', 'error')
        return redirect(url_for('login'))

@app.route('/delete_application/<application_id>', methods=['POST'])
def delete_application(application_id):
    if session.get('id') and session.get('role') == 'student':
        try:
            application_collection = db.application
            application_id = ObjectId(application_id)
            application_collection.delete_one({'_id': application_id})

            co_guides_selected = db.co_guides_selected.find_one({"application_id": ObjectId(application_id)})

            if co_guides_selected:
                db.co_guides_selected.delete_many({"application_id": ObjectId(application_id)})

            flash('Application deleted successfully.', 'success')
        except:
            flash('Failed to delete the application.', 'error')
        
        return redirect(url_for('list_and_delete_applications'))
    else:
        flash('Please login as a student to view your applications.', 'error')
        return redirect(url_for('login'))


@app.route('/select_co_guides/<application_id>', methods=['GET', 'POST'])
def select_co_guides(application_id):
    if session.get('role') == 'faculty':
        if request.method == 'POST':
            co_guides_selected = request.form.getlist('co_guides[]')

            # Save the selected co-guides for the application
            co_guides_collection = db.co_guides_selected
            co_guides_collection.insert_one({
                "application_id": ObjectId(application_id),
                "co_guides_selected": co_guides_selected
                # "status": "Pending"
            })

            # Update the status of the application to 'Approved by Guide'
            application_collection = db.application
            application_collection.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": {"status": "Approved by Guide"}}
            )

            flash('Co-guides selected successfully', 'success')
            return redirect('/application_list')  # Redirect to application list or any other appropriate page
        else:
            # Fetch student's roll_no from the application
            roll_no = db.application.find_one({"_id": ObjectId(application_id)})['roll_no']

            # Fetch student's department using the roll_no
            student_dept = db.users.find_one({"id": roll_no})['department']

            # Fetch faculties from the student's department
            co_guides = db.users.find({"role": "faculty", "department": student_dept})
            return render_template('select_co_guides.html', co_guides=co_guides, application_id=application_id)
    else:
        flash('Please login as a faculty to select co-guides.', 'error')
        return redirect(url_for('login'))


@app.route('/view_selected_co_guides/<application_id>', methods=['GET', 'POST'])
def view_selected_co_guides(application_id):
    if session.get('role') == 'student':
        co_guides_collection = db.co_guides_selected
        selected_co_guides = co_guides_collection.find_one({"application_id": ObjectId(application_id)})
        if selected_co_guides:
            co_guides = selected_co_guides.get("co_guides_selected", [])
            print(co_guides)
            if 'any' in co_guides:
                co_guides.remove('any')  # Remove 'any' from the list of selected co-guides
                # Fetch user's roll number from the application ID
                application = db.application.find_one({"_id": ObjectId(application_id)})
                roll_no = application.get("roll_no")
                if roll_no:
                    # Fetch user's department using the roll number
                    user = db.users.find_one({"id": roll_no})
                    department = user.get("department")
                    if department:
                        # Fetch all faculties from the department
                        all_faculties = db.users.find({"role": "faculty", "department": department})
                        # Convert the cursor to a list of dictionaries
                        co_guides = list(all_faculties)
                        return render_template('apply_to_co_guide.html', co_guides=co_guides, application_id=application_id)
                    else:
                        flash('Department information not found for the user', 'error')
                        return redirect('/btp_list')  # Redirect to BTP list or any other appropriate page
                else:
                    flash('Roll number not found for the application', 'error')
                    return redirect('/btp_list')  # Redirect to BTP list or any other appropriate page
            else:
                temp = []
                for c in co_guides:
                    user = db.users.find_one({"_id": ObjectId(c)})
                    if user:
                        temp.append({"_id": c, "full_name": user.get('full_name')})
                return render_template('apply_to_co_guide.html', co_guides=temp, application_id=application_id)
        else:
            flash('No co-guides selected yet', 'error')
            return redirect('/btp_list')  # Redirect to BTP list or any other appropriate page
    else:
        flash('Please login as a student to view selected co-guides.', 'error')
        return redirect(url_for('login'))



@app.route('/send_applications_to_co_guides/<application_id>', methods=['POST'])
def send_applications_to_co_guides(application_id):
    if request.method == 'POST':
        # Assuming you have a form in apply_to_co_guide.html where users select co-guides
        # Retrieve the selected co-guides from the form
        selected_co_guides = request.form.getlist('co_guides[]')
        # Now, you can store applications for each selected co-guide in the database
        co_guides_collection = db.co_guides_selected
        
        # Delete existing co-guides selected for the given application ID
        co_guides_collection.delete_many({"application_id": ObjectId(application_id)})
        
        # Insert new documents for the selected co-guides
        for co_guide_id in selected_co_guides:
            # Insert a new document for each co-guide application
            co_guides_collection.insert_one({
                "application_id": ObjectId(application_id),
                "co_guide_id": co_guide_id,
                "status": "Applied"  # Assuming you want to set status to 'Applied'
            })

            application_collection = db.application
            application_collection.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": {"status": "Applied for Co-Guide"}}
            )
        
        flash('Applications sent to selected co-guides successfully.', 'success')
        return redirect('/btp_list')  # Redirect to BTP list or any other appropriate page

    else:
        flash('Invalid request method.', 'error')
        return redirect('/btp_list')  # Redirect to BTP list or any other appropriate page


@app.route('/co_guide_applications')
def co_guide_applications():
    if session.get('id') and session.get('role') == "faculty":
        # Fetch applications for the current co-guide from the database
        id = db.users.find_one({"id": session['id']}).get("_id")
        co_guides_selected = db.co_guides_selected.find({"co_guide_id": str(id)})
        applications = []  # Initialize an empty list
        
        for c in co_guides_selected:
            application = db.application.find_one({"_id": c['application_id']})  # Use find_one instead of find
            if application:
                btp_proj = db.btp_list.find_one({"btp_id": application['btp_id']})
                application['btp_name'] = btp_proj['btp_name']
                faculty = db.users.find_one({"id": btp_proj['prof_id']})
                application['faculty_name'] = faculty['full_name']
                application['faculty_email'] = faculty['email']
                applications.append(application)
        return render_template('co_guide_applications.html', applications=applications)
    else:
        flash('Access denied.', 'error')
        return redirect('/')  # Redirect to login page or any other appropriate page

@app.route('/approve_application/<application_id>', methods=['POST', 'GET'])
def approve_application(application_id):
    if session.get('id') and session.get('role') == "faculty":
        id = db.users.find_one({"id": session['id']}).get("_id")
        application = db.co_guides_selected.find_one({"application_id": ObjectId(application_id), "co_guide_id": str(id)})
        if application:
            # Update the status of the application to 'Approved'
            db.co_guides_selected.update_many({"application_id": ObjectId(application_id)}, {"$set": {"status": "Approved"}})

            db.co_guides_selected.delete_many({"application_id": ObjectId(application_id),"status": {"$ne": "Approved"}})
            
            # Update the status of the application to 'Approved' in the application collection
            db.application.update_many({"_id": ObjectId(application_id)}, {"$set": {"status": "Approved"}})
            flash('Application approved successfully.', 'success')
        else:
            flash('Application not found or you do not have permission to approve it.', 'error')
        return redirect('/co_guide_applications')  # Redirect back to the applications page
    else:
        flash('Access denied.', 'error')
        return redirect('/')  # Redirect to login page or any other appropriate page
    
@app.route('/logout')
def logout():
    # Clear the session when user logs out
    session.pop('id', None)
    session.pop('role', None)
    flash('You have been logged out', 'success')
    return redirect('/')

@app.route('/view_users')
def view_users():
    if session.get('role') == 'admin':
        users_collection = db.users
        all_users = users_collection.find()
        users_list = []
        for user in all_users:
            if user['role'] == 'admin':
                continue
            user_details = {
                '_id': user.get('_id', ''),
                'id': user.get('id', ''),
                'full_name': user.get('full_name', ''),
                'email': user.get('email', ''),
                'department': user.get('department', ''),
                'role': user.get('role', '')
            }
            users_list.append(user_details)
        # print(users_list)
        return render_template('view_users.html', users=users_list)
    else:
        flash('Unauthorized access. Please login as admin.', 'error')
        return redirect(url_for('login'))


@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') == 'admin':
        try:
            user_id = ObjectId(user_id)
        except:
            flash('Invalid user ID.', 'error')
            return redirect(url_for('admin_home'))

        try:
            users_collection = db.users

            # Find the user by ID
            user = users_collection.find_one({"_id": user_id})
            if not user:
                flash('User not found.', 'error')
                return redirect(url_for('admin_home'))

            # Delete the user
            users_collection.delete_one({"_id": user_id})

            # Delete related documents from other collections
            # Example: If the user has projects, delete them from the projects collection
            btp_collection = db.btp_list
            btp_collection.delete_many({"prof_id": user_id})

            # Example: If there are applications associated with the user, delete them
            application_collection = db.application
            application_collection.delete_many({"roll_no": user['id']})

            # Example: If there are co-guides associated with the user, delete them
            co_guides_collection = db.co_guides_selected
            co_guides_collection.delete_many({"co_guides_selected": user_id})
            co_guides_collection.delete_many({"co_guides_selected": {"$in": [user_id]}})

            flash('User and related information deleted successfully.', 'success')
            return redirect(url_for('view_users'))
        except Exception as e:
            flash(f'An error occurred while deleting the user: {str(e)}', 'error')
            return redirect(url_for('admin_home'))
    else:
        flash('Unauthorized access. Please login as admin.', 'error')
        return redirect(url_for('login'))

@app.route('/confirm_project', methods=['GET', 'POST'])
def confirm_project():
    if session.get('role') == 'student':
        if request.method == 'POST':
            selected_project_id = request.form.get('project_id')
            roll_no = session.get('id')

            if not selected_project_id:
                flash('Please select a project to confirm.', 'error')
                return redirect(url_for('student_home'))

            try:
                application_collection = db.application

                # Update the status of all projects associated with the student to "Pending" except the selected one
                application_collection.update_many({"roll_no": roll_no, "status": "Temporarily Confirmed", "btp_id": {"$ne": selected_project_id}},
                                                    {"$set": {"status": "Approved"}})

                # Update the status of the selected project to "Confirmed"
                application_collection.update_one({"roll_no": roll_no, "status": "Approved", "btp_id": selected_project_id},
                                                  {"$set": {"status": "Temporarily Confirmed"}})

                flash('Project confirmed successfully.', 'success')
                return redirect(url_for('student_home'))
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('student_home'))
        else:
            try:
                roll_no = session.get('id')
                application_collection = db.application
                btp_list_collection = db.btp_list

                # Fetch the student's projects with status "Approved"
                student_projects = application_collection.find({"roll_no": roll_no, "status": "Approved"})

                # Extract btp_id from the projects
                btp_ids = [project["btp_id"] for project in student_projects]

                # Fetch the btp_name for each btp_id from the btp_list collection
                projects_info = []
                for btp_id in btp_ids:
                    btp_info = btp_list_collection.find_one({"btp_id": btp_id})
                    if btp_info:
                        projects_info.append({"btp_id": btp_id, "btp_name": btp_info.get("btp_name", "Unknown")})

                return render_template('confirm_project.html', projects=projects_info)
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('student_home'))
    else:
        flash('Unauthorized access. Please login as a student.', 'error')
        return redirect(url_for('login'))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask_mail import Mail, Message

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'testemailskgp@gmail.com'
app.config['MAIL_PASSWORD'] = 'rlfm iyro bnpe zexv'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

department_emails = {
    "CSE": "paramanandabhaskar@gmail.com",
    "ECE": "paramanandabhaskar@gmail.com",
    "ME": "me_dept@example.com",
    "CE": "ce_dept@example.com",
    "AE": "ae_dept@example.com",
    "MBA": "mba_dept@example.com"
}

@app.route('/send_email')
def send_email():
    if session.get('id') and session.get('role') == 'student':
        users_collection = db.users
        application_collection = db.application
        btp_collection = db.btp_list
        user_roll_no = session.get('id')
        applications = application_collection.find({"roll_no": user_roll_no, "status": "Temporarily Confirmed"})
        
        for application in applications:

            btp_id = application.get("btp_id")
            btp = btp_collection.find_one({"btp_id": btp_id})
            prof = users_collection.find_one({"id": btp["prof_id"]})
            stud = users_collection.find_one({"id": user_roll_no})

            data = {
                "btp_id": btp_id,
                "btp_name": btp["btp_name"],
                "name": stud["full_name"],
                "dep": stud["department"],
                "prof_name": prof["full_name"],
                "faculty_name": prof["full_name"]
            }

            # Get co-guide name
            co_guide = db.co_guides_selected.find_one({"application_id": application["_id"]})
            if co_guide:
                co_guide_id = co_guide.get('co_guide_id')
                co_guide_user = users_collection.find_one({"_id": ObjectId(co_guide_id)})
                data['coguide_name'] = co_guide_user.get('full_name', 'No name provided') if co_guide_user else 'User not found'
            else:
                data['coguide_name'] = 'No co-guide assigned'

            # Generate PDF
            pdf_filename = f"{btp_id}.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=letter)
            c.drawString(100, 780, f"BTP Id: {btp_id}")
            c.drawString(100, 760, f"BTP NAME: {data['btp_name']}")
            c.drawString(100, 740, f"Name: {data['name']}")
            c.drawString(100, 720, f"Department: {data['dep']}")
            c.drawString(100, 700, f"Co-Guide Name: {data['coguide_name']}")
            c.drawString(100, 680, f"Faculty Name: {data['faculty_name']}")
            c.save()

            # Send email
            recipient_email = department_emails.get(data["dep"], "default_email@example.com")
            msg = Message("BTP Application",
                          sender= "testemailskgp@gmail.com",
                          recipients=[recipient_email])
            msg.body = "Please find the attached PDF for the BTP application."
            with open(pdf_filename, "rb") as fp:
                msg.attach(pdf_filename, "application/pdf", fp.read())
            
            mail.send(msg)
            application_collection.update_one(
                {"_id": application["_id"]},
                {"$set": {"status": "Confirmed"}}
            )
            # Add the student to the project in btp_list
            db.btp_list.update_one({"btp_id": btp_id},
                                            {"$addToSet": {"students": user_roll_no}})

        return redirect(url_for('login'))
    else:
        flash('Please login as a student to send applications to HOD.', 'error')
        return redirect(url_for('login'))
    

@app.route('/view_projects', methods=['GET'])
def view_projects():
    if session.get('role') == 'faculty':
        guide_id = session.get('id')
        projects = db.btp_list.find({"prof_id": guide_id})
        return render_template('view_projects.html', projects=projects)
    else:
        flash('Unauthorized access. Please login as faculty.', 'error')
        return redirect(url_for('login'))

from datetime import datetime
@app.route('/set_submission_details/<btp_id>', methods=['GET', 'POST'])
def set_submission_details(btp_id):
    if session.get('role') == 'faculty':
        if request.method == 'POST':
            try:
                submission_deadline = datetime.strptime(request.form.get('submission_deadline'), '%Y-%m-%d %H:%M')
                full_marks = (request.form.get('full_marks'))
                
                students = request.form.getlist('students')
                submission_details = []
                for roll_no in students:
                    detail = {
                        "btp_id": btp_id,
                        "roll_no": roll_no,
                        "submission_deadline": submission_deadline,
                        "full_marks": full_marks
                    }
                    submission_details.append(detail)
                db.btp_submission_collection.insert_many(submission_details)
                
                flash('Submission details set successfully.', 'success')
                return redirect(url_for('view_projects'))
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('view_projects'))
        else:
            # Fetch students associated with the project and pass them to the template
            project = db.btp_list.find_one({"btp_id": btp_id})
            students = project.get('students', [])
            context = {
                'btp_id': btp_id,
                'students': students
            }
            return render_template('set_submission_details.html', context=context)
    else:
        flash('Unauthorized access. Please login as faculty.', 'error')
        return redirect(url_for('login'))


@app.route('/submit_report/<btp_id>/<roll_no>', methods=['GET', 'POST'])
def submit_report(btp_id, roll_no):
    if session.get('role') == 'student':
        if request.method == 'POST':
            try:
                report_file = request.files['report_file']
                if report_file:
                    # Save the report file to GridFS
                    file_id = fs.put(report_file, filename=f"{btp_id}_{roll_no}_{secure_filename(report_file.filename)}")
                    
                    # Update the submission details in the database if exists, otherwise insert
                    db.btp_submission_collection.update_one(
                        {"btp_id": btp_id, "roll_no": roll_no},
                        {"$set": {"file_id": file_id, "submitted": True}},
                        upsert=True
                    )

                    flash('Report submitted successfully.', 'success')
                    return redirect(url_for('student_home'))
                else:
                    flash('No report file selected.', 'error')
                    return redirect(url_for('submit_report', btp_id=btp_id, roll_no=roll_no))
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('submit_report', btp_id=btp_id, roll_no=roll_no))
        else:
            # Render the form for submitting the report
            return render_template('submit_report.html', btp_id=btp_id, roll_no=roll_no)
    else:
        flash('Unauthorized access. Please login as a student.', 'error')
        return redirect(url_for('login'))

@app.route('/marks_submissions/<btp_id>/<roll_no>', methods=['GET', 'POST'])
def marks_submissions(btp_id, roll_no):
    if session.get('role') == 'faculty':
        if request.method == 'POST':
            try:
                # Get the marks from the form
                marks = request.form.get('marks')

                # Update the marks in the database
                db.btp_submission_collection.update_one(
                    {"btp_id": btp_id, "roll_no": roll_no},
                    {"$set": {"marks": marks}}
                )

                flash('Marks updated successfully.', 'success')
                return redirect(url_for('faculty_home'))
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('faculty_home'))
        else:
            # Fetch submission details for the specific student and project
            submission = db.btp_submission_collection.find_one({"btp_id": btp_id, "roll_no": roll_no})

            if submission:
                return render_template('marks_submissions.html', submission=submission)
            else:
                flash('Submission not found.', 'error')
                return redirect(url_for('faculty_home'))
    else:
        flash('Unauthorized access. Please login as faculty.', 'error')
        return redirect(url_for('login'))

@app.route('/view_marks/<btp_id>/<roll_no>', methods=['GET'])
def view_marks(btp_id, roll_no):
    # Check if the user is logged in and has the correct role
    if session.get('role') == 'student' and session.get('id') == roll_no:
        # Fetch the marks for the specified btp_id and roll_no from the database
        marks = db.marks_submission_collection.find_one({"btp_id": btp_id, "roll_no": roll_no})
        
        if marks:
            return render_template('view_marks.html', marks=marks)
        else:
            flash('Marks not found.', 'error')
            return redirect(url_for('student_home'))
    elif session.get('role') == 'faculty':
        # Check if the faculty member is associated with the specified BTP project
        project = db.btp_list.find_one({"btp_id": btp_id, "prof_id": session.get('id')})
        if project:
            # Fetch the marks for the specified btp_id and roll_no from the database
            marks = db.marks_submission_collection.find_one({"btp_id": btp_id, "roll_no": roll_no})
            
            if marks:
                return render_template('view_marks.html', marks=marks)
            else:
                flash('Marks not found.', 'error')
                return redirect(url_for('faculty_home'))
        else:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('faculty_home'))
    else:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))

    
if __name__ == "__main__":
    app.run(debug=True)