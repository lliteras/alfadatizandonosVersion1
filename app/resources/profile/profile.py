from flask import redirect, render_template, request, url_for, session, abort, flash, jsonify
from flask_session import Session
from models.user import User
from models.establishment import Establishment

def get_my_profile():
	if session['id']:
		user = User.get_information_of_user(session['id'])
		establishments = User.get_establishments_of_user(session['id'])
		provincias = Establishment.select_provinces()
		return render_template('profile/profile.html', user=user, establishments=establishments, provincias = provincias)
	return render_template(url_for('home'))

def addInstitute():
	if session['id']:
		establishment = request.form['instituteFormControlSelect']
		User.add_institute(session['id'], establishment)
		return redirect(url_for('profile'))
	return render_template(url_for('home'))