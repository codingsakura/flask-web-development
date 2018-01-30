import os
from flask import Flask, render_template, session, redirect, url_for
from flask_script import Manager, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_mail import Mail, Message

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
	'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
#SQLALCHEMY_TRACK_MODIFICATIONS = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <codingsakura@gmail.com>'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'hard to guess string'
manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
mail = Mail(app)

class NameForm(FlaskForm):
	name = StringField('What is your name?', validators = [Required()])
	submit = SubmitField('Submit')

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(64), unique = True)

	def __repr__(self):
		return '<Role %r>' % self.name
	users = db.relationship('User', backref = 'role')

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(64), unique = True, index = True)

	def __repr__(self):
		return '<User %r>' % self.username
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

@app.route('/', methods = ['GET', 'POST'])
def index():
	form = NameForm()
	if form.validate_on_submit():
		#session['name'] = form.name.data
		user = User.query.filter_by(username = form.name.data).first()
		if user is None:
			user = User(username = form.name.data)
			db.session.add(user)
			session['known'] = False
			if app.config['FLASKY_ADMIN']:
				send_email(app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user = user)
		else:
			session['known'] = True
		session['name'] = form.name.data
		form.name.data = ''
		return redirect(url_for('index'))
	return render_template('index.html', form = form, name = session.get('name'), known = session.get('known', False))

@app.route('/user/<name>')
def user(name):
	return render_template('user.html', name = name)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500

def make_shell_context():
	return dict(app = app, db = db, User = User, Role = Role)
manager.add_command('shell', Shell(make_context = make_shell_context))
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

def send_email(to, subject, template, **kwargs):
	msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, sender = app.config['FLASKY_MAIL_SENDER'], recipients = [to])
	msg.body = render_template(template + '.txt', **kwargs)
	msg.html = render_template(template + '.html', **kwargs)
	mail.send(msg)

if __name__=='__main__':
	manager.run()