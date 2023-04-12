from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import numpy as np
import pandas as pd
import pyodbc

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    subjectid = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"Professor('{self.name}', '{self.username}', '{self.password}')"


with app.app_context():
    db.create_all()

cnxn = pyodbc.connect('DRIVER={SQL Server};'
                      'SERVER=tcp:facercgntn.database.windows.net;'
                      'DATABASE=Attendance_Database;UID=face_recognition;PWD=fnrcgntn123@#;')
cursor = cnxn.cursor()


@app.route('/')
@app.route('/login', methods=['POST', 'GET'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        account = Professor.query.filter_by(username=username, password=password).first()
        if account:
            return redirect('/show/' + account.subjectid)
        else:
            msg = 'Incorrect username / password!'
    return render_template('login.html', msg=msg)


@app.route('/show/<subjectid>', methods=['GET'])
def show(subjectid):
    date = datetime.today().strftime('%m-%d-%Y')
    query = "Select student_id, student_name, subject_name, status, day, attendance_capture_time " \
            "from [attendance] " \
            "where day = DATENAME(weekday, GETDATE()) and " \
            "subject_name = '" + subjectid + "'"
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    df1 = pd.DataFrame.from_records(rows, columns=columns)
    global df
    df = df1
    print(df)
    return render_template('show.html', rows=df.iterrows(), date=date)


@app.route('/change/<int:rollno>')
def change(rollno):
    print(rollno)
    print(df)
    subject_name = df.loc[df['student_id'] == rollno, 'subject_name'].iloc[0]
    print(subject_name)
    if df.loc[df['student_id'] == rollno, 'status'].iloc[0] == 'Present':
        df.loc[df['student_id'] == rollno, 'status'] = 'Absent'
        status = "Absent"
        att_time = "NULL"
        df.loc[df['student_id'] == rollno, 'attendance_capture_time'] = att_time
    else:
        df.loc[df['student_id'] == rollno, 'status'] = 'Present'
        status = "Present"
        att_time = "'" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "'"
        df.loc[df['student_id'] == rollno, 'attendance_capture_time'] = att_time
    query = "UPDATE [attendance]" \
            "SET status = '" + status + "', attendance_capture_time = " + att_time + \
            " WHERE student_id = " + str(rollno) + " and subject_name = '" + subject_name + "'"
    cursor.execute(query)
    cnxn.commit()
    return redirect('/show/' + subject_name)


if __name__ == '__main__':
    app.run()