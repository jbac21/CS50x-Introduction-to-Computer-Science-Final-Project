# Module import
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

import calendar
import numpy
import pandas as pd
from datetime import date, datetime
from dateutil.rrule import rrule, DAILY

from helpers import apology, login_required


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///vector.db")


# Define global variables
# Set working days
DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
    ]

# List of selectable vaccines
VACCINES = [
    "BioNTech",
    "Moderna",
    "AstraZeneca"
    ]

# View on the index page for offices
offerBox = ['block', 'none']


# Flask Routes
# Index page
@app.route("/", methods=["GET", "POST"])
@login_required
def index(DAYS=DAYS):

    # Get username from session
    username = session.get("user_id")

    # Get user and account information
    user = db.execute("SELECT calluser, account FROM user WHERE username = ?", username)[0] # database request
    name = user['calluser'] # get the name to be shown on html page
    account = user['account'] # get account type to forward the user to the respective index page

    # Patients: index_patient.html
    if account == 'patient':

        # POST requests
        if request.method == "POST":

            # Set transaction - Only a prototype, better check availability before booking again
            db.execute("BEGIN TRANSACTION")

            # Get information from form
            appointmentid = request.form.get("appointmentid")

            # Get username form session
            username = session.get("user_id")

            # Get the number of patients being already registered
            appointmentData = db.execute("SELECT booked FROM appointment WHERE appointmentid = ?", appointmentid)
            nbpersons = appointmentData[0]['booked'] + 1 # increase by one for the current booking

            # Update database
            db.execute("UPDATE appointment SET booked = ? WHERE appointmentid = ?", nbpersons, appointmentid)
            db.execute("UPDATE patient SET appointmentid = ? WHERE username = ?", appointmentid, username)

            # End Transaction
            db.execute("COMMIT")

        # GET requests
        else:
            # Initiliaze appointmentData as an empty list
            appointmentData = [{}]

        # GET & POST requests

        # Check if user has an appointment and set variable which enables the book button on index_patient.html
        appointmentId = db.execute("SELECT appointmentid FROM patient WHERE username = ?", username)[0]['appointmentid']
        bookingEnabler = [' impossible',' impossible'] # Initialize
        # If not yet booked - enable booking
        if appointmentId == "" or appointmentId == None:
            bookingEnabler[0] = "possible"
        # If already booked - book buttons are greyed out and deactivated
        else:
            bookingEnabler[1] = "possible"

        # Get available appointment information
        schedule = db.execute("SELECT username, institution, appointmentid, date, time, personnb, booked FROM appointment JOIN office ON appointment.usernameoffice = office.username ORDER BY usernameoffice")
        df2 = pd.DataFrame(schedule) # Create dataframe with information
        df2av= df2[df2['personnb']>df2['booked']] # Filter available appointments
        htmldf = df2av.T.to_dict().values() # Create dict including the results

        #Iterate over results to adjust the date formatting
        for entry in htmldf:
            entry['date'] = datetime.strptime(entry['date'],"%Y-%m-%d %H:%M:%S").date()

        # Set information if appointment has been scheduled
        if appointmentId != "" and appointmentId != None: # Condition: Has appointment id
            appointmentData = db.execute("SELECT * FROM appointment WHERE appointmentid = ?", appointmentId)[0] # Get all information about an appointment
            usernameoffice = appointmentData['usernameoffice'] # Get the name of the office
            appointmentData['date'] = datetime.strptime(appointmentData['date'],"%Y-%m-%d %H:%M:%S").date() # Adjust the data format
            information = db.execute("SELECT * FROM office WHERE username = ?", usernameoffice)[0] # Get all personal information about the office

        # Set information for GET if no appointment has been scheduled
        else:
            information = {}

        # Render the html page for patients
        return render_template("index_patient.html", name=name, df=htmldf, enabler=bookingEnabler, information=information, information2=appointmentData)


    # Offices: index_offices.html
    else:
        # Define global variables
        global offerBox # Determines the view of the tabs

        # Get all appointments for the user which have been already booked.
        appointmentData = db.execute("SELECT * FROM appointment WHERE usernameoffice = ? AND booked > 0 ORDER BY date, time", username)

        # No appointments have been booked
        if len(appointmentData) == 0:
            schedule = {}

        # Appointments have been booked
        else:
            # Iterate over appointments
            for appointment in appointmentData:
                appointment['date'] = datetime.strptime(appointment['date'],"%Y-%m-%d %H:%M:%S").date() # Adjust the format of the date
                appointmentid = appointment['appointmentid'] # Set the appointment id
                user = db.execute("SELECT * FROM patient WHERE appointmentid = ?", appointmentid) # Get patient personal data
                if len(user) != 0: # If there are user information
                    user = user[0] # Select the user from the retrieved data list
                    # Define user information
                    appointment['patientfirstname'] = user['firstname']
                    appointment['patientlastname'] = user['lastname']
                    appointment['patientstreet'] = user['street']
                    appointment['patienthousenb'] = user['housenb']
                    appointment['patientpostalcode'] = user['postalcode']
                    appointment['patientcity'] = user['city']
                    appointment['patientphone'] = user['phone']
                    appointment['patientmail'] = user['mail']

                    # Convert vaccine preferences into text to be shown in html
                    vaccineList = []
                    # Deleting preferences of the previous user
                    text=""

                    # Set vaccine preferences in list
                    if user['biontech'] == "like":
                        vaccineList.append("BioNTech")

                    if user['astrazeneca'] == "like":
                        vaccineList.append("AstraZeneca")

                    if user['moderna'] == "like":
                        vaccineList.append("Moderna")

                    # Generate text for html form
                    if len(vaccineList) > 0:
                        text = vaccineList[0]
                        for entry in vaccineList[1:]: # Iterate over prefered vaccines
                            text = text + ", " + str(entry)
                    appointment['patientvaccine'] = text # Add text to dict (input for html)

            # Appointment data ready for html rendering
            schedule = appointmentData

        # Get all appointments of the offer including appointments not being booked yet
        appointmentOffer = db.execute("SELECT * FROM appointment WHERE usernameoffice = ? ORDER BY date, time", username)

        # Iterate over appointments and prepare output
        for appointment in appointmentOffer:
            appointment['date'] = datetime.strptime(appointment['date'],"%Y-%m-%d %H:%M:%S").date() # Adjust formatting of dates

            # Set color for appointment booking status - green: no booking, yellow: some bookings, red: all booked
            if appointment['booked'] == 0 or appointment['booked'] == "": # Available
                appointment['booked'] = "rgb(187,231,32)"
            elif appointment['booked'] > 0 and appointment['booked'] < appointment['personnb']: # Some have booked
                appointment['booked'] = "orange"
            if appointment['booked'] == appointment['personnb']: # Not available anymore
                appointment['booked'] = "red"

        # Render the html page for offices
        return render_template("index_office.html", name=name, schedule=schedule, offer=appointmentOffer, days=DAYS, box=offerBox)


# Function for adding new appointments to database
def dbadd_appointment(username):

    # Define global variables
    global offerBox # Variable determining the view on the html page

    # Set box in case index-page is shown after function, shows 'Offer' tab
    offerBox = ['none','block']

    # Set scope of available appointments
    days_input = request.form.getlist("days[]") # First field disabled & selected
    times = request.form.getlist("time[]")[1:]
    persons = request.form.getlist("personnb[]")[1:]

    # Case that no scope for available appointments is set (during registration)
    if days_input == []:
        times =[]
        persons=[]

    # Create dataframe using the user input
    days = {'weekday': days_input, 'times': times, 'persons': persons}
    df = pd.DataFrame(data=days)

    # Set periode
    if len(days_input) > 0:
        startdate = datetime.strptime(request.form.getlist("startdate")[0],"%Y-%m-%d")
        enddate = datetime.strptime(request.form.getlist("enddate")[0],"%Y-%m-%d")

        startdate = startdate.date()
        enddate = enddate.date()

        # Iterate over each day in periode
        for single_date in rrule(DAILY, dtstart=startdate, until=enddate):

            # Define & emtpy lists for filtered times and nb of persons
            searchTimes = []
            searchPersons = []

            # Filter weekday information
            weekday = calendar.day_name[single_date.weekday()] # Determine weekday for date
            search = df[df.weekday == weekday] # Filter dataframe by weekday
            searchTimes = search['times'].tolist() # Get times for the weekday

            # If no appointments for that day, skip and continue
            if len(searchTimes) == 0:
                continue

            # If appointments
            else:
                # Create a list with the number of persons who can book the appointment
                searchPersons = search['persons'].tolist()

            # Get a unique appointment ID
            maxAppointmentid = None # Initialize

            # Iterate over all new appointments
            for i in range(0, len(searchTimes)):

                # Define variables for database entry
                time = searchTimes[i] # Time of appointment
                personnb = searchPersons[i] # Persons being able to book the appointment

                # Check if appointment id is already defined (relevance due to for loop)
                try: maxAppointmentid
                except NameError: maxAppointmentid = None

                # If first iteration (for loop) > Get database information
                if maxAppointmentid == None:
                    maxAppointmentid = db.execute("SELECT * FROM appointment ORDER BY appointmentid DESC")

                    # If there are no entries in database, set appointment id 1
                    if maxAppointmentid == []:
                        maxAppointmentid = 1

                    # Else increment by one
                    else:
                        maxAppointmentid = maxAppointmentid[0]['appointmentid']
                        maxAppointmentid += 1

                # For 2 - n iterations: Increment appointmentID
                else:
                    maxAppointmentid += 1

                # Insert information into database
                db.execute("INSERT INTO appointment (usernameoffice, date, time, personnb, appointmentid) VALUES (?, ?, ?, ?, ?)", username, single_date, time, personnb, maxAppointmentid)


# Route for deleting appointments
@app.route("/appointmentDelete/", methods=["GET","POST"])
def delete_appointment():

    # Define global variables
    global offerBox # Variable determining the view on the html page

    # GET request > Go to login or index page
    if request.method == "GET":
        return redirect("/")

    # POST request
    else:

        # Set box in case index-page is shown after function, shows 'Offer' tab
        offerBox = ['none','block']

        # Get appointment id to be deleted from form (element hidden from view)
        item = request.form.get("appointmentid")

        # Adjust database
        db.execute("UPDATE patient SET appointmentid = ? WHERE appointmentid = ?", "", item) # User has no appointment
        db.execute("DELETE FROM appointment WHERE appointmentid = ?", item) # Appointment does no longer exist

        # Return to index page
        return redirect("/")


# Route for creating new appointments
@app.route("/newAppointment/", methods=["GET","POST"])
def new_appointment():

    # Forward to login or index if GET
    if request.method == "GET":
        return redirect("/")

    # POST
    else:
        # Get username
        username = session.get("user_id")
        # Call function for creating a new appointment for the user
        dbadd_appointment(username=username)

        # Return to index page
        return redirect("/")


# Route for patient index page
@app.route("/index_patient")
def index_patient():

    # Redirect to login / index
    return redirect("/")


# Route for office index page
@app.route("/index_office")
def index_office():

    # Redirect to login / index
    return redirect("/")


# Login for users - thanks to CS50 Finance application
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM user WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/login.html")


# Logout for users - thanks to CS50 Finance application
@app.route("/logout")
def logout():
    """Log user out"""
    global offerBox

    # Reset  view of index
    offerBox = ['block', 'none']

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# Route for registering users
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Caching user input in case of an error
    registration = []
    error = []

    # GET - load the page
    if request.method == "GET":

        # Define global variables
        global VACCINES

        # Render page
        return render_template("register.html", vaccines=VACCINES, error=error, registration=registration)

    # POST - Register user
    else:

        # Get user data
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        street = request.form.get("street")
        housenb = request.form.get("house_number")
        postalcode = request.form.get("zip")
        city = request.form.get("city")
        phone = request.form.get("phone")
        mail = request.form.get("mail")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        registration.extend([firstname, lastname, street, housenb, postalcode, city, phone, mail, username, password, confirmation])

        # Check for missing values in user form
        description = ['firstname', 'lastname', 'street', 'house number', 'postal code', 'city', 'phone number', 'mail adress', 'username', 'password', 'password confirmation']
        missing = []

        # Create dictionary including information from registration form and labels
        dictionary = dict(zip(description, registration))

        # Iterate over form elements and check for values
        for key in dictionary:
            # If no value add to missing and error
            if dictionary[key] == '':
                missing.append(key) # List for flush
                error.append("error") # Parameterlist for formatting html form elements - error
            # If value exists
            else:
                error.append("") # Parameterlist for formatting html form elements - no error

        # User input not complete
        if len(missing) != 0:

            # Create text for error message
            text = str(missing[0])
            for element in missing[1:]:
                text = text + ", " + str(element)

            # Flash text to user on page
            flash('Error: No ' + str(text) + ' entered.', "danger")

            # Render html page include vaccine selection, previous user form input, error formatting of form elements
            return render_template("register.html", vaccines=VACCINES, registration=registration[0:8], error=error)

        # Error check: username already exists
        elif len(db.execute("SELECT * FROM user WHERE username = ?", str(username))) != 0:

            # Mark form element red
            error = ['','','','','','','','', 'error']

            # Flash error message
            flash('Error: Username already in use.', "danger")

            # Render html page include vaccine selection, previous user form input, error formatting of form elements
            return render_template("register.html", vaccines=VACCINES, registration=registration[0:8], error=error)


        # Error: check if password and confirmed password do not match
        elif str(password) != str(confirmation):
            # Mark form element red
            error = ['','','','','','','','','','error','error']

            # Flash error message
            flash('Error: Passwords do not match.', "danger")

            # Render html page include vaccine selection, previous user form input, error formatting of form elements
            return render_template("register.html", vaccines=VACCINES, registration=registration[0:8], error=error)

        # Save credentials and personal data to db
        else:
            # create hash for password
            hashpw = generate_password_hash(str(password), method='pbkdf2:sha256', salt_length=8)

            # Get information from radios
            vaccine = request.form.get("registerRadios")

            # Set vaccine preferences according to radio button choice
            if vaccine == "all": # Value is all
                vaccine1 = "like"
                vaccine2 = "like"
                vaccine3 = "like"

            elif vaccine == None: # Not selected
                vaccine1 = ""
                vaccine2 = ""
                vaccine3 = ""

            # Set vaccine preferences if individually selected
            else: # Value select
                # Get all user input from forms, list extendable via js
                vaccine = request.form.getlist("vaccines[]")

                # Initialize variables for prefered vaccines
                vaccine1 = ""
                vaccine2 = ""
                vaccine3 = ""

                # Define variables for database entry
                for entry in vaccine:
                    if entry == "BioNTech":
                        vaccine1 = "like"

                    elif entry == "AstraZeneca":
                        vaccine2 = "like"

                    elif entry == "Moderna":
                        vaccine3 = "like"

                # Set account type & username
                account = "patient"
                calluser = firstname

                # Save user information in database
                db.execute("INSERT INTO patient (username, firstname, lastname, street, housenb, postalcode, city, phone, mail, biontech, astrazeneca, moderna) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", username, firstname, lastname, street, housenb, postalcode, city, phone, mail, vaccine1, vaccine2, vaccine3)
                db.execute("INSERT INTO user (username, hash, account, calluser) VALUES(?, ?, ?, ?)", username, hashpw, account, calluser)

    # Flash user information
    flash('User account has been created successfully. Please login.', "success")

    # Render template
    return render_template("/login.html")


# Register offices
@app.route("/offer", methods=["GET", "POST"])
def offer():

    # Cache User Input
    registration = []
    error = []

    # Define global variables
    global DAYS
    global VACCINES

    # GET - Show register page
    if request.method == "GET":
        # Render page
        return render_template("offer.html", vaccines=VACCINES, days=DAYS, registration=registration, error=error)

    # POST - Register office (optimization potential - parts are also included in patient registration process)
    else:
        # Get user personal data from form
        institution = request.form.get("institution")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        street = request.form.get("street")
        housenb = request.form.get("house_number")
        postalcode = request.form.get("zip")
        city = request.form.get("city")
        phone = request.form.get("phone")
        mail = request.form.get("mail")
        vaccine = request.form.getlist("vaccines[]")
        vaccineAmount = request.form.getlist("vaccines_amount[]")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Add data to list
        registration.extend([institution, firstname, lastname, street, housenb, postalcode, city, phone, mail, username, password, confirmation])

        # Check for missing values in user form
        description = ['institution', 'firstname', 'lastname', 'street', 'house number', 'postal code', 'city', 'phone number', 'mail adress', 'username', 'password', 'password confirmation']
        # Create dictionary with user's personal data and label
        dictionary = dict(zip(description, registration))

        # Initilize lists for error handling
        missing = []
        error = []

        # Iterate over dictionary in check for missing user input
        for key in dictionary:

            # If value from input is missing
            if dictionary[key] == '':
                missing.append(key) # Append to list - used for error message
                error.append("error") # Append to list - used for highlighting error input fields

            # No value is missing
            else:
                error.append("") # Append to list - no adjustment of html class information

        # If data are missing
        if len(missing) != 0:

            # Create error text
            text = str(missing[0])
            for element in missing[1:]:
                text = text + ", " + str(element)

            # Flash error message
            flash('Error: No ' + str(text) + ' entered.', "danger")

            # Render html page include vaccine selection, days for appointments, previous user form input, error formatting of form elements
            return render_template("offer.html", vaccines=VACCINES, days=DAYS, registration=registration[0:9], error=error)

        # Error check: username already exists
        elif len(db.execute("SELECT * FROM user WHERE username = ?", str(username))) != 0:

            # Mark form element red
            error = ['','','','','','','','','','error']

            # Flash error message
            flash("username already in use", "danger")

            # Render html page include vaccine selection, days for appointments, previous user form input, error formatting of form elements
            return render_template("offer.html", vaccines=VACCINES, days=DAYS, registration=registration[0:9], error=error)

        # check if password and confirmed password do not match
        if str(password) != str(confirmation):

            # Mark form element red
            error = ['','','','','','','','','','','error','error']

            # Flash error message
            flash("passwords do not match", "danger")

            # Render html page include vaccine selection, days for appointments, previous user form input, error formatting of form elements
            return render_template("offer.html", vaccines=VACCINES, days=DAYS, registration=registration[0:9], error=error)

        # Save credentials and personal data to db
        else:

            # create hash for password
            hashpw = generate_password_hash(str(password), method='pbkdf2:sha256', salt_length=8)

            # Prepare variables for prefered vaccines
            vaccine1 = ""
            vaccine2 = ""
            vaccine3 = ""

            # Set available number of vaccines - Not implemented beyond the registration due to time limitations
            vaccine1nb = 0
            vaccine2nb = 0
            vaccine3nb = 0

            # Prepare database input for vaccines
            for entry in vaccine:
                if entry == "BioNTech":
                    vaccine1 = "like"
                    vaccine1nb = vaccineAmount[vaccine.index(entry) + 1]

                elif entry == "AstraZeneca":
                    vaccine2 = "like"
                    vaccine2nb = vaccineAmount[vaccine.index(entry) + 1]

                elif entry == "Moderna":
                    vaccine3 = "like"
                    vaccine3nb = vaccineAmount[vaccine.index(entry) + 1]

            # Set account type
            account = "office"

            # Set user name for html page
            calluser = institution

            # Create new appointments for user
            dbadd_appointment(username=username)

            # Save user information in database
            db.execute("INSERT INTO office (institution, username, firstname, lastname, street, housenb, postalcode, city, phone, mail, biontech, astrazeneca, moderna, biontechnb, astrazenecanb, modernanb) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", institution, username, firstname, lastname, street, housenb, postalcode, city, phone, mail, vaccine1, vaccine2, vaccine3, vaccine1nb, vaccine2nb, vaccine3nb)
            db.execute("INSERT INTO user (username, hash, account, calluser) VALUES(?, ?, ?, ?)", username, hashpw, account, calluser)

    # Flash message
    flash('User account has been created successfully. Please login.', "success")

    # Render template for login
    return render_template("/login.html")

# Error handler - thanks to CS50 Finance application
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors - thanks to CS50 Finance application
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
