from flask import redirect, render_template, request, url_for, session, abort, flash
from db import get_db
from models.activity import Activity
from models.dataset import Dataset
from models.course import Course
from models.user import User
from datetime import date
import datetime


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


		return render_template('activities/solve_activity.html', activity=activity, activityId=id, datasetId=datasetId, socialGraph=socialGraph, plotterTab=plotterTab, resolutions=resolutions)

def addPlotterResolutionToActivity():

	if request.method=="POST":

		#information of resolution
		commentary = request.form['commentary']
		activityId = request.form['activityId']
		userId = session['id']
		resolutionType = 'plotter'
		dateTimeNow = datetime.datetime.now()


		resolution_id = Activity.inset_resolution(activityId, userId, resolutionType, dateTimeNow ,commentary)


		
		#Information of plotter resolution
		y_axis = ''
		stringCondition = ''

		selection = request.form['selection']
		x_axis = request.form['x_axis']

		plotterResolutionFields='graph_type, x_axis'
		plotterResolutionFieldsValues = '\''+selection + '\', \'' + x_axis


		if request.form.get('y_axis'):

			y_axis = request.form['y_axis']

			plotterResolutionFields= plotterResolutionFields + ', y_axis'
			plotterResolutionFieldsValues = plotterResolutionFieldsValues + '\', \'' + y_axis



		dispersion_x = request.form['dispersion_x']
		dispersion_y = request.form['dispersion_y']
		cumulative = request.form['cumulative']
		has_condition = request.form['has_condition']
		datasetId = request.form['datasetId']	

		plotterResolutionFields= plotterResolutionFields + ', dispersion_x, dispersion_y, cumulative, has_condition, id_dataset, id_resolution'
		plotterResolutionFieldsValues = plotterResolutionFieldsValues + '\', \'' + dispersion_x
		plotterResolutionFieldsValues = plotterResolutionFieldsValues + '\', \'' + dispersion_y
		plotterResolutionFieldsValues = plotterResolutionFieldsValues + '\', \'' + str(cumulative)
		plotterResolutionFieldsValues = plotterResolutionFieldsValues + '\', \'' + str(has_condition)
		plotterResolutionFieldsValues = plotterResolutionFieldsValues + '\', \'' + str(datasetId)
		plotterResolutionFieldsValues = plotterResolutionFieldsValues + '\', \'' + str(resolution_id)+'\''


		plotter_resolution_id = Activity.insert_resolution_plotter(plotterResolutionFields, plotterResolutionFieldsValues)

		

		#Conditions
		if has_condition:

			stringCondition = request.form['stringCondition']

			Activity.insert_resolution_plotter_conditions(stringCondition, plotter_resolution_id)



	return ''

def addSocialGraphResolutionToActivity():

	if request.method=="POST":

		#information of resolution
		commentary = request.form['commentary']
		activityId = request.form['activityId']
		userId = session['id']
		resolutionType = 'social graph'
		dateTimeNow = datetime.datetime.now()

		resolution_id = Activity.inset_resolution(activityId, userId, resolutionType, dateTimeNow ,commentary)

		#Information of social graph resolution

		searchString = request.form['searchString']
		excludePrepositions = request.form['excludePrepositions']
		excludeArticles = request.form['excludeArticles']
		excludePronouns = request.form['excludePronouns']
		excludeConjunctions = request.form['excludeConjunctions']
		excludeAdverbs = request.form['excludeAdverbs']
		excludeVerbs = request.form['excludeVerbs']
		excludeLinks = request.form['excludeLinks']
		quantityOfWords = request.form['quantityOfWords']
		cloudBase64 = request.form['cloudBase64']
		plotterBase64 = request.form['plotterBase64']

		

		Activity.insert_resolution_social_graph(resolution_id, searchString, excludePrepositions, excludeArticles, excludePronouns, excludeConjunctions, excludeAdverbs, excludeVerbs, excludeLinks, quantityOfWords, cloudBase64, plotterBase64)






	return ''


def viewResolutionGraph(resolutionId):

	resolution = Activity.get_resolution(resolutionId)

	plotterResolution = Activity.get_plotter_resolution(resolutionId)

	dataset = Dataset.get_dataset(plotterResolution['id_dataset'])

	datasetName = dataset['name']

	plotterResolution['x_axis_to_show'] = plotterResolution['x_axis'].split('***')[len(plotterResolution['x_axis'].split('***'))-1] 

	if plotterResolution['y_axis']:

		plotterResolution['y_axis_to_show'] = plotterResolution['y_axis'].split('***')[len(plotterResolution['y_axis'].split('***'))-1] 

	plotterResolutionConditions	= []

	if plotterResolution['has_condition']:

		plotterResolutionConditions = Activity.get_plotter_resolution_conditions(plotterResolution['id_resolution_plotter'])

		for condition in plotterResolutionConditions:

			stringConditionField = condition['condition']

			stringCondition = ''

			if ' >= ' in stringConditionField and ' <= ' in stringConditionField:

				stringCondition =  stringConditionField.split('***')[1]

				stringCondition = stringCondition.split(' and ')[0]

				stringCondition = stringCondition + ' y ' + stringConditionField.split('***')[len(stringConditionField.split('***'))-1]

				

			else:

				stringCondition	= stringConditionField.split('***')[len(stringConditionField.split('***'))-1]

			condition['stringCondition'] = stringCondition	





	return render_template('activities/view_resolution_graph.html', noNav=True, datasetName=datasetName, plotterResolution=plotterResolution, conditions=plotterResolutionConditions )

def viewResolutionSocialGraph(resolutionId):

	resolution = Activity.get_resolution(resolutionId)

	socialGraphResolution = Activity.get_social_graph_resolution(resolutionId)

	return render_template('activities/view_resolution_social_graph.html', noNav=True, resolution=resolution, socialGraph=socialGraphResolution)


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

