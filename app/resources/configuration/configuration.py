from flask import redirect, render_template, request, url_for, session, abort, flash, jsonify, current_app as app
from db import get_db
from models.user import User
from models.activity import Activity
from werkzeug.utils import secure_filename
from models.configuration import Configuration
import os, shutil
import json

pagination = 10	

def configuration():
	if session['username']:
		configuration_data = Configuration.get_file_data()
		aux = User.get_all_users_with_pagination(pagination, 1, 0)
		users = aux[0]
		maxPage = aux[1]
		availablePages = getAvailablePages(1, maxPage)
		dictionary = {}
		for user in users:
			roles = User.get_roles_of_user(user['id'])
			dictionary[user['id']] = [role['role_id'] for role in roles]

		return render_template('configuration/configuration.html', data=configuration_data, users=users, roles=dictionary,availablePages=availablePages, maxPage=maxPage, actualPage=1)
	else:
		return redirect(url_for('home'))

def configuration_AJAX(page,filtered):
	if session['username']:
		aux = User.get_all_users_with_pagination(pagination, page, filtered)
		users = aux[0]
		maxPage = aux[1]
		availablePages = getAvailablePages(page, maxPage)
		dictionary = {}
		for user in users:
			roles = User.get_roles_of_user(user['id'])
			dictionary[user['id']] = [role['role_id'] for role in roles]
		return jsonify(result=users, roles=dictionary, availablePages=availablePages)

	return redirect(url_for('home'))


UPLOAD_FOLDER = 'static/establecimientos_educativos/'
ALLOWED_EXTENSIONS = set(['csv'])

def upload_establishment_file():
	if request.method == 'POST':
		
		folder = os.path.join(UPLOAD_FOLDER)

		file = request.files['file']

		filename = secure_filename(file.filename)
		
		if file and allowed_file(filename):

			filePath = ""
			for fname in os.listdir(folder):
				filePath = os.path.join(folder, fname)
			if filePath:
				try:
					if os.path.isfile(filePath) or os.path.islink(filePath):
						os.unlink(filePath)
					elif os.path.isdir(filePath):
						shutil.rmtree(filePath)
				except Exception as e:
					print('Error al cargar %s. Razón: %s' % (filePath, e))

			file.save(folder + filename)
			Configuration.add_file_data(filename)

	return redirect(url_for('home'))
	


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def cambiar_rol(user_id, role_id):
	if session['username'] and session['role']=="admin":
		Configuration.change_role(user_id, role_id)
	return False

def add_role(role_id, user_id):
	if session['actualRole']=='admin' or session['actualRole']=='superadmin':
		Configuration.add_role(user_id, role_id)
	return jsonify(True)

def delete_role(role_id, user_id):
	if session['actualRole']=='admin' or session['actualRole']=='superadmin':
		Configuration.delete_role(user_id, role_id)
	return jsonify(True)

def getAvailablePages(actualPage, maxPage):

	pagesArray = []

	if maxPage > 4:

		if actualPage < 4:
			
			pagesArray = [1,2,3,4,5]

		else:

			if maxPage >= actualPage+2:

				pagesArray = [actualPage-2, actualPage-1, actualPage, actualPage + 1, actualPage + 2]

			else:
				
				pagesArray = [maxPage - 4, maxPage - 3, maxPage - 2, maxPage - 1, maxPage]	
	else:

		for x in range(maxPage):

			pagesArray.append(x+1)		

	return pagesArray	