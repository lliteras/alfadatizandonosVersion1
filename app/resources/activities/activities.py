from flask import redirect, render_template, request, url_for, session, abort, flash, jsonify
from sqlalchemy import null
from db import get_db
from models.activity import Activity
from models.dataset import Dataset
from models.course import Course
from models.user import User
from datetime import date
from werkzeug.utils import secure_filename
import os
import datetime

UPLOAD_FOLDER = 'static/uploads/resolutions'

def activities():
	if session['name']:
		activities = Activity.getMyActivities(session['id'])
		finished_activities = []
		current_activities = []
		overdue_activities = []
		undelivered_activities = []
		corrected_activities = []

		for activity in activities:
			if activity['calification']:
				corrected_activities.append(activity)
			else: 
				if not activity['enable_expired_date'] and (activity['end_date']  < date.today()):
					undelivered_activities.append(activity)
				else:
					if 'date_resolution' in activity.keys():
						finished_activities.append(activity)
					else:
						if activity['enable_expired_date'] and (activity['end_date']<date.today()):
							overdue_activities.append(activity)
						else:
							current_activities.append(activity)
		return render_template('activities/activities.html', activities=activities, current_activities=current_activities, finished_activities=finished_activities, overdue_activities=overdue_activities, undelivered_activities=undelivered_activities, corrected_activities=corrected_activities, today=date.today(), user_id=session['id'])
	else:
		return render_template('/')

def new_activity(course_id, **kwargs):
	if session['actualRole'] == "professor":
		graficos = Activity.get_graph_names()

		datasets = datasets = Course.get_dataset_by_courseId(course_id)

		students = User.get_user_from_course(course_id)

		emptyFields = kwargs.get('emptyFields', "")
		errorGraficos = kwargs.get('errorGraficos', "")
		errorFechas = kwargs.get('errorFechas', "")
		fecha_comienzo = kwargs.get('startDate', "")
		fecha_fin = kwargs.get('endDate', "")
		titulo = kwargs.get('title', "")
		descripcion = kwargs.get('description',"")
		objective= kwargs.get('objective', "")
		has_calification = kwargs.get('has_calification', "")
		statement = kwargs.get('statement', "")
		statement_title = kwargs.get('statement_title', "")
		datasetId = kwargs.get('datasetId', "")
		students_id=kwargs.get('students_id',"")
		enable_expired_date=kwargs.get('enable_expired_date', "")
		student_select = kwargs.get('student_select', "")
		socialGraph = kwargs.get('socialGraph', "")
		checked_graphs = kwargs.get('graphs', "")

		return render_template('activities/new_activity.html', course_id=course_id, graphs=graficos, datasets=datasets, students=students, emptyFields=emptyFields, errorGraficos=errorGraficos, errorFechas=errorFechas, startDate=fecha_comienzo, endDate=fecha_fin, title=titulo, description=descripcion, objective=objective, has_calification=has_calification, statement=statement, statement_title=statement_title, datasetId=datasetId, students_id=students_id, enable_expired_date=enable_expired_date,  student_select=student_select, socialGraph=socialGraph, checked_graphs=checked_graphs)
	else:
		return redirect(url_for('home'))

def create_activity():
	if request.method=="POST":
		if 'title' in request.form and 'startDate' in request.form and 'endDate' in request.form and  'description'  in request.form and  'objective' in request.form and  'inputStatement' in request.form and  'inputStatementTitle' in request.form and 'datasetSelect' in request.form:
			fecha_comienzo = request.form['startDate']
			fecha_fin = request.form['endDate']
			titulo = request.form['title']
			descripcion = request.form['description']
			curso = request.form['course']
			graphs = request.form.getlist('graph')
			objective = request.form['objective']
			has_calification = not('checkboxNoCalification' in request.form)
			enable_expired_date = 'checkboxExpiredDate' in request.form
			statement = request.form['inputStatement']
			statement_title = request.form['inputStatementTitle']
			student_select = request.form['student_select']
			students_id = request.form.getlist('student_checkbox')
			datasetId = request.form['datasetSelect']
			socialGraph = False
			if request.form.get('checkboxSocialGraph'):
				socialGraph = request.form.get('checkboxSocialGraph')
				if socialGraph == 'on':
					socialGraph = True
			if fecha_comienzo=="" or fecha_fin =="" or descripcion=="" or objective=="" or statement=="" or statement_title=="" or datasetId =="":
				return new_activity(request.form['course'], emptyFields="Todos los campos son necesarios", startDate=fecha_comienzo, endDate=fecha_fin, title=titulo, description=descripcion, objective=objective, has_calification=has_calification, statement=statement, statement_title=statement_title, datasetId=datasetId, students_id=students_id, enable_expired_date=enable_expired_date, student_select=student_select, socialGraph=socialGraph, graphs=graphs)	
			if not graphs:
				return new_activity(curso, errorGraficos="Debe seleccionar al menos una visualización disponible.", startDate=fecha_comienzo, endDate=fecha_fin, title=titulo, description=descripcion, objective=objective, has_calification=has_calification, statement=statement, statement_title=statement_title, datasetId=datasetId, students_id=students_id, enable_expired_date=enable_expired_date, student_select=student_select, socialGraph=socialGraph, graphs=graphs)
			fecha_comienzo = datetime.datetime.strptime(fecha_comienzo, '%Y-%m-%d')
			fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d')
			if fecha_fin<fecha_comienzo:
				return new_activity(curso, errorFechas="La fecha de comienzo debe ser menor a la de fin.", title=titulo, description=descripcion, objective=objective, has_calification=has_calification, statement=statement, statement_title=statement_title, datasetId=datasetId, students_id=students_id, enable_expired_date=enable_expired_date,  student_select=student_select, socialGraph=socialGraph, graphs=graphs)
			Activity.create_activity(fecha_comienzo, fecha_fin, titulo, descripcion, curso, graphs, objective, has_calification, enable_expired_date, statement_title, statement, students_id, datasetId, socialGraph)
			return redirect('/courses/' + curso, code=302)
		return new_activity(request.form['course'], emptyFields="Todos los campos son necesarios", startDate=fecha_comienzo, endDate=fecha_fin, title=titulo, description=descripcion, objective=objective, has_calification=has_calification, statement=statement, statement_title=statement_title, datasetId=datasetId, students_id=students_id, enable_expired_date=enable_expired_date,  student_select=student_select, socialGraph=socialGraph, graphs=graphs)
	return redirect(url_for('home'))

def view_activity_data(id):
	if session['id']:
		actividad = Activity.get_activity_by_id(id)
		graficos_disponibles = Activity.get_graph_of_activity_by_id(id)
		alumnos = Activity.get_students_from_activity(id)


		return render_template('activities/activity_view_data.html', activity=actividad, available_graphs=graficos_disponibles, students=alumnos)

def view_activity(id):
	if session['id']:
		actividad = Activity.get_activity_by_id(id)
		return render_template('activities/activity_view.html', activity=actividad, noNav=True)

def solveActivity(id):
	if session['id']:
		activity = Activity.get_activity_by_id(id)
		datasetId= activity['dataset_id']
		
		socialGraph = activity['social_graph']

		resolutions = Activity.get_user_activity_resolution(session['id'], id)



		graphs = Activity.get_graph_of_activity_by_id(id)
		plotterTab = len(graphs) != 0

		user = User.get_information_of_user(session['id'])

		return render_template('activities/solve_activity.html', activity=activity, activityId=id, datasetId=datasetId, socialGraph=socialGraph, plotterTab=plotterTab, resolutions=resolutions, user=user)

def isPDF(filename):
	return filename.split(".")[1] == "pdf"

def addResolutionToActivity():

	if request.method=="POST":

		#information of resolution
		commentary = request.form['commentary']
		activityId = request.form['activityId']
		userId = session['id']
		resolutionType = 'plotter'
		dateTimeNow = datetime.datetime.now()
		try:
			file = request.files.get('file')
		except KeyError:
			data = {
						"message": 'Compruebe el archivo subido',
						"status": 400
				}
			return  jsonify(data), 400
			
		if file:
				filename = secure_filename(file.filename)		
				if isPDF(filename):
					id = Activity.inset_resolution(activityId, userId, resolutionType, dateTimeNow ,commentary)
					file.save(os.path.join(UPLOAD_FOLDER, "resolution_" + str(id) + 'pdf'))
					data = {
							"message": 'Respuesta cargada correctamente.',
							"status": 200
					}
					return  jsonify(data), 200
				else:
					data = {
								"message": 'Compruebe el archivo subido',
								"status": 400
						}
					return  jsonify(data), 400
		else:
			data = {
						"message": 'Compruebe el archivo subido',
						"status": 400
				}
			return  jsonify(data), 400

def correct_activity_view(activity_id, user_id):
	if session['id']:
		activity = Activity.get_activity_by_id(activity_id)
		alumno = Activity.get_activity_of_student(activity_id, user_id)

		resolutions = Activity.get_user_activity_resolution(user_id, activity_id)

		return render_template('activities/correct_activity.html', activity=activity, student=alumno, resolutions=resolutions)

def viewCorrectedActivity(activity_id, user_id):
	if session['id']:
		activity = Activity.get_activity_by_id(activity_id)
		
		alumno = Activity.get_activity_of_student(activity_id, user_id)

		resolutions = Activity.get_user_activity_resolution(user_id, activity_id)

		return render_template('activities/view_corrected_activity.html', activity=activity, student=alumno, resolutions=resolutions)

def correct_activity(activity_id, user_id):
	if request.method=="POST":
		comentario = request.form['comment']
		if request.form.get('calification'):
			nota = request.form['calification']
		else:
			nota = -1
		Activity.correct_activity(activity_id, user_id, nota, comentario)
		return redirect(url_for('view_activity_data', id=activity_id))

	return redirect(url_for('home'))

