#encoding=utf-8
import os, time, copy
from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_script import Manager, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required, DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'waf.db')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username

class t_TestSuite(db.Model):
    __tablename__ = 't_testsuite'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String)
    start_time = db.Column(db.Integer)
    end_time = db.Column(db.Integer)
    current_case = db.Column(db.String)
    case_run = db.Column(db.String)
    case_pass = db.Column(db.Integer)
    case_fail = db.Column(db.Integer)
    case_abort = db.Column(db.Integer)
    case_total = db.Column(db.Integer)

class t_TestCases(db.Model):
    __tablename__ = 't_testcases'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String)
    start_time = db.Column(db.Integer)
    end_time = db.Column(db.Integer)
    state = db.Column(db.String)
    step_run = db.Column(db.Integer)
    step_pass = db.Column(db.Integer)
    step_fail = db.Column(db.Integer)
    total = db.Column(db.Integer)
    ts_id = db.Column(db.Integer, db.ForeignKey('t_testsuite.id'))

class t_TestSteps(db.Model):
    __tablename__ = 't_teststeps'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String)
    testlink_id = db.Column(db.String)
    spec = db.Column(db.String)
    result = db.Column(db.Integer)
    tc_id = db.Column(db.Integer, db.ForeignKey('t_testcases.id'))


# from caiadmin import CaiAdmin
# ca=  CaiAdmin(app, db, [t_TestSuite, t_TestCases, t_TestSteps])
# ca.init_app()
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, t_TestSuite=t_TestSuite, t_TestCases=t_TestCases, t_TestSteps=t_TestSteps)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

def db_handle(list):
    rd = {
    0: 'Pass',
    1: 'Fail',
    2: 'Abort',
    11: 'Topo Fail',
    12: 'Connect Fail',
    }
    list = copy.deepcopy(list)
    for d in list:
        if d.__tablename__ == 't_testsuite' or d.__tablename__ == 't_testcases':
            d.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(d.start_time))
            d.end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(d.end_time))
        elif d.__tablename__ == 't_teststeps':
            d.result = rd[d.result]
    return list

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/')
def main():
    return render_template('main.html')

@app.route('/waf/', methods=['GET', 'POST'])
def waf():
    if request.method == "POST":
        attribute = request.form.get("attribute")
        value = request.form.get("value")
        if attribute and value:
            if attribute == "id":
                ts_suite = t_TestSuite.query.filter_by(id=value).first()
                if ts_suite is None:
                    flash("Not found the taskid is %s"%value)
                    return redirect(url_for('waf'))
                return redirect(url_for('testsuite', attribute=attribute,value=value))
            elif attribute == "name":
                ts_suite = t_TestSuite.query.filter_by(name=value).first()
                if ts_suite is None:
                    flash("Not found the taskname is %s"%value)
                    return redirect(url_for('waf'))
                return redirect(url_for('testsuite', attribute=attribute,value=value))
        else:
            flash("Please input what you want tu search before submit") 
            return redirect(url_for('waf'))
    return render_template('waf.html')

@app.route('/waf/testsuite/')
def testsuite():
    att, val = request.args.get('attribute'), request.args.get('value')
    l = []
    if att == "id":
        l = t_TestSuite.query.filter_by(id=val).all()
    elif att == "name":
        l = t_TestSuite.query.filter_by(name=val).all()
    elif att == "all":
        l = t_TestSuite.query.all()
    l = db_handle(l)
    return render_template('testsuite.html', l=l)

@app.route('/waf/testcases/')
def testcases():
    ts_id = request.args.get('ts_id')
    l = t_TestCases.query.filter_by(ts_id=ts_id).all()
    l = db_handle(l)
    return render_template('testcases.html', l=l)

@app.route('/waf/teststeps/')
def teststeps():
    tc_id = request.args.get('tc_id')
    l = t_TestSteps.query.filter_by(tc_id=tc_id).all()
    l = db_handle(l)
    return render_template('teststeps.html', l=l)

if __name__ == '__main__':
    manager.run()
