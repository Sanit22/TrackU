from app import app, db
from flask import render_template, redirect, flash, url_for, request, session, send_file
from .forms import *
from .models import User,Tracker,Logs, Settings, options
from sqlalchemy.exc import IntegrityError
from sqlalchemy  import exc, insert
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone
import calendar
from calendar import month_abbr
from matplotlib import pyplot as plt
import base64
from io import BytesIO
from matplotlib.figure import Figure

bcrypt = Bcrypt(app)


# months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
# years = []
# start = 1995
# for i in range(start, 2030):
#     years.append(str(i))


@app.route('/')
def index():
    login_form = Login_form()
    sign_up_form = Sign_up_form()
    return render_template('index.html', login_form = login_form, sign_up_form = sign_up_form)

@app.route('/sign-up', methods=["POST"])
def signup():
    form = Sign_up_form()
    print("INSIDE SIGN UPP")
    if(form.validate_on_submit()):
        name = form.name.data
        email = form.email.data
        password = form.password.data
        try:
            new_user = User(name, email, password)
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('User already exists')
            return redirect(url_for('index'))
        session['user_id'] = new_user.id
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials! Please try again.')
        print(form.errors)
        return redirect(url_for('index'))

@app.route('/login', methods=["POST"])
def login():
    error = None
    login_form = Login_form()
    if login_form.validate_on_submit():

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email = email).first()
        if(user):
            pw_hash = user.password
            if(bcrypt.check_password_hash(pw_hash, password)):
                print("INSIDE VALID PASSWORD**")
                session['user_id'] = user.id
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email/password!', 'error')
                return render_template('index.html', login_form = login_form)
        else:
            print("INSIDE INVALID USERNAME/PASS")
            error = 'Invalid email/password!'
            return render_template('index.html', error=error, login_form = login_form)
    else:
        flash('Something went wrong!', 'error')
        return render_template('index.html', login_form = login_form)





@app.route('/dashboard')
def dashboard():
    print(session)
    if(session.get('user_id')):
        x = [5,8,19,40,3,9]
        y = [12,5,8,45,2,53]
        fig = Figure()
        ax = fig.subplots()
        ax.plot(x,y)
        # Save it to a temporary buffer.
        buf = BytesIO()
        fig.savefig(buf, format="png")
        # Embed the result in the html output.
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        trackers = Tracker.query.filter_by(user_id=session['user_id']).all()
        #create a dict of tracker id and lastlogged
        last_logged = dict()
        for tracker in trackers:
            tracker_id = tracker.id
            allLogs = list(tracker.logs)
            if(len(allLogs) > 0):
                date_time = allLogs[-1].timestamp.split('T')
                timestamp = date_time[0] + " " + "at" + " " + date_time[1]
                last_logged[tracker_id] = timestamp
            else:
                last_logged[tracker_id] = "No logs yet!"
    
        username = User.query.filter_by(id=session['user_id']).first().username
        print("UTC NOW", datetime.utcnow())
        print("timezone", datetime.now(timezone.utc)) 
        curr_time = datetime.utcnow()
        print(type(curr_time))
        print(type(curr_time.strftime("%b-%-d %-I:%-M %p")))
        month_num = datetime.now().month
        print(month_abbr[month_num])

        return render_template('dashboard.html', trackers = trackers, data=data, username=username, last_logged=last_logged)    
    else:
        flash('Please login/signup')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session['user_id'] = None
    return redirect(url_for('index'))   

@app.route('/create_tracker')
def create_tracker():
    form = Create_tracker_form()
    return render_template('tracker_form.html', form = form)

@app.route('/add_tracker', methods = ['GET', 'POST'])
def add_tracker():
    form = Create_tracker_form()
    if form.validate_on_submit():

        print("FORM VALIDATED****")
        name = form.name.data
        tracker_type = form.tracker_type.data
        
        description = form.description.data
        if(tracker_type == 'Boolean'):
            tracker_settings = 'Yes,No'
        else:
            tracker_settings = form.tracker_settings.data
        tracker_settings = tracker_settings.split(',')
        user_id = session['user_id']
        try:
            new_tracker = Tracker(name, description, tracker_type, user_id)
            db.session.add(new_tracker)
            db.session.commit()
            #if any setting already exists -- no need to add it
            settings_query = Settings.query.all()
            setting_list = []
            for setting in settings_query:
                setting_list.append(setting.name)
            for setting in tracker_settings:
                if(setting in setting_list):
                    new_setting = Settings.query.filter_by(name=setting).first()
                else:
                    new_setting = Settings(setting)
                    db.session.add(new_setting)
                    db.session.commit()
                #add to the table options
                new_tracker.settings.append(new_setting)
                db.session.commit()
            

        except exc.SQLAlchemyError as e:
            db.session.rollback()
            print(type(e))
            raise(e)
            flash('ERROR --  Make sure the tracker has a unique name')
            return redirect(url_for('create_tracker'))
        return redirect(url_for('dashboard'))
    else:
        print("FORM INVALIDATED****")
        flash('Invalid form data')
        return redirect(url_for('create_tracker'))
    
@app.route('/create_log/<tracker_id>', methods = ['GET', 'POST'])
def create_log(tracker_id):
    form = Create_log_form()
    tracker = Tracker.query.filter_by(id=tracker_id).first()
    timestamp = datetime.utcnow()
    timestamp = timestamp.strftime("%Y-%m-%dT%H:%M")
    for setting in tracker.settings:
        print(setting.name)
    return render_template('create_log_form.html', form = form, tracker = tracker, timestamp=timestamp)

@app.route('/add_log/<tracker_id>', methods=['GET', 'POST'])
def add_log(tracker_id):

    form = Create_log_form()
    tracker = Tracker.query.filter_by(id=tracker_id).first()
    if( form.validate_on_submit()):
        #validate choices for multiple choice and boolean
        settings = tracker.settings
        setting_list = []
        for setting in settings:
            setting_list.append(setting.name)
        print(setting_list)
        print(form.data)
        value = form.value.data
        timestamp = form.timestamp.data
        print(value)
        if(tracker.tracker_type == 'Multiple Choice' or tracker.tracker_type == 'Boolean'):
            if(value not in setting_list):
                flash('Invalid form data. Please refill.')
                return redirect(url_for('create_log', tracker_id=tracker_id))
        try:
            new_log = Logs(form.note.data, value, tracker_id, timestamp)
            db.session.add(new_log)
            datetime = timestamp.split('T')
            last_logged = datetime[0] + "at" + datetime[1]
            print(last_logged)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            print(type(e))
            db.session.rollback()
            flash('ERROR OCCURRED WHILE ADDING LOG')
            return redirect(url_for('create_log', tracker_id=tracker_id))
        
        #update to viewlogs url and add a message 'log added successfully'
        return redirect(url_for('view_logs', tracker_id=tracker_id))

@app.route('/delete_tracker/<tracker_id>')
def delete_tracker(tracker_id):
    tracker = Tracker.query.filter_by(id=tracker_id).first()
    if(tracker):
        db.session.delete(tracker)
        db.session.commit()
        flash('Tracker deleted successfully')
        #TO DO --if any other tracker is not sharing these settings -- delete them
        return redirect(url_for('dashboard'))
    else:
        flash('Deletion error. Please try again')
        return redirect(url_for('dashboard'))

@app.route('/view_logs/<tracker_id>')
def view_logs(tracker_id):
    tracker = Tracker.query.filter_by(id=tracker_id).first()
    if(tracker):
        logs = tracker.logs
        # add scatter plot
        values = []
        dates = []
        for log in logs:
            values.append(log.value)
            date = log.timestamp.split('T')[0]
            date = date.split('-')
            month = month_abbr[int(date[1])]
            day = date[2]
            date = day + '-' + month
            dates.append(date)
        fig = Figure()
        ax = fig.subplots()
        ax.plot(values,dates)
        ax.set_xlabel('Values')
        ax.set_ylabel('Dates')
        # Save it to a temporary buffer.
        buf = BytesIO() 
        fig.savefig(buf, format="png")
        # Embed the result in the html output.
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        return render_template('view_logs.html', logs = logs, tracker_id=tracker_id, data=data)
    else:
        flash('Error in viewing logs')
        return redirect(url_for('dashboard'))

@app.route('/delete_log/<tracker_id>/<log_id>')
def delete_log(tracker_id, log_id):
    log = Logs.query.filter_by(id=log_id).first()
    try:
        db.session.delete(log)
        db.session.commit()
        flash('Log deleted successfully')
    except:
        flash('Error in deleting log')
    return redirect(url_for('view_logs', tracker_id=tracker_id))

@app.route('/edit_tracker/<tracker_id>', methods=['GET', 'POST'])
def edit_tracker(tracker_id):
    form = Create_tracker_form()
    tracker = Tracker.query.filter_by(id=tracker_id).first()
    time_settings = ['hours', 'minutes']
    

    if(request.method == 'POST' and form.validate_on_submit()):
        print(form.data)
        tracker = Tracker.query.filter_by(id=tracker_id).first()
        tracker.name = form.name.data
        tracker.description = form.description.data
        if(tracker.tracker_type != form.tracker_type.data):
            tracker.tracker_type = form.tracker_type.data
            #remove all logs
            logs = tracker.logs
            for log in logs:
                db.session.delete(log)
                db.session.commit()

        #remove(unlink) all existing settings
        
        curr_settings = tracker.settings
        print(curr_settings)
        for setting in curr_settings:
            print("Set -- ", setting.name)
            tracker.settings.remove(setting)
        print(tracker.settings)
        #if its a new setting add it to settings else don't
        settings_list = []
        if(form.tracker_type.data == 'Boolean'):
            settings_list = ['Yes', 'No']
        elif(form.tracker_type.data == 'Numerical'):
            setting_data = form.tracker_settings.data
            settings_list.append(setting_data)
        elif(form.tracker_type.data == 'Multiple Choice' or form.tracker_type.data == 'Time Duration'):
            setting_data = form.tracker_settings.data
            print(setting_data)
            settings_list = setting_data.split(',')
        print(settings_list)
        for setting in settings_list:
            #query the setting -- if found add to tracker else create a new setting 
            new_setting = Settings.query.filter_by(name=setting).first()
            if(not new_setting):
                new_setting = Settings(setting)
                db.session.add(new_setting)
                db.session.commit()
            tracker.settings.append(new_setting)
            db.session.commit()

        return redirect(url_for('dashboard'))
    # else:
    #     flash('Invalid form data -- Could not be edited')
    #     return redirect(url_for('edit_tracker', tracker_id = tracker.id))



    #give me a pre filled tracker form and the ability to make changes
    #what will happen to the logs if u change the tracker type
    # if tracker type changes -- give the user a warning that all his logs will be deleted -- if yes delete all
    print("FORM NOT VALIDATED ** ")
    form.name.data = tracker.name
    form.tracker_type.data = tracker.tracker_type
    form.description.data = tracker.description
    setting_str = ""
    for setting in tracker.settings:
        setting_str += setting.name + ','
    setting_str = setting_str[:-1]
    form.tracker_settings.data = setting_str
    
    return render_template('edit_tracker.html', form = form, tracker_id=tracker_id)


@app.route('/edit_log/<log_id>', methods=['GET', 'POST'])
def edit_log(log_id):
    form = Create_log_form()
    log = Logs.query.filter_by(id=log_id).first()

    if(form.validate_on_submit()):
        try:
            log.note = form.note.data
            log.value = form.value.data
            #this is a temporary solution to creating and editing timestamps
            log.timestamp = form.timestamp.data
            db.session.commit()
        except exc.SQLAlchemyError as e:
            print(type(e))
            flash('error in editing log')
            return redirect(url_for('/edit_log', log_id=log_id))
        return redirect(url_for('dashboard'))

    form.note.data = log.note
    form.value.data = log.value
    timestamp = log.timestamp
    
    
    return render_template('edit_log.html', form=form, log_id=log_id, timestamp=timestamp)  
