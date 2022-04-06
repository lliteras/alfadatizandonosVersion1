from flask import redirect, jsonify, render_template, request, url_for, session, abort, flash
from db import get_db
from models.course import Course
from models.activity import Activity
from models.dataset import Dataset
from models.user import User
from datetime import date
import datetime

def get_courses():
	if session['actualRole'] == "professor":
		cursos = Course.get_my_courses(session['id'])
		return render_template('course/courses.html', cursos=cursos)
	else:
		return redirect(url_for('home'))

def new_course():
	if session['actualRole'] == "professor":
		curricularScopes = get_curricular_scope()
		establishments = User.get_establishments_of_user(session['id'])
		return render_template('course/new_course.html', curricularScopes=curricularScopes, establishments=establishments)
	else:
		return redirect(url_for('home'))

def create_course():
	if request.method=="POST":
		curricularScopes = get_curricular_scope()
		establishments = User.get_establishments_of_user(session['id'])
		if 'name' in request.form and 'startDate' in request.form and 'endDate' in request.form:
			nombre = request.form['name']
			fecha_comienzo = request.form['startDate']
			fecha_fin = request.form['endDate']
			establismentId = request.form['inputEstablishment']
			cicle = request.form['inputCiclo']
			if cicle and cicle=='1':
				year = request.form['inputAnioBasico']
			elif cicle=='2':
				year = request.form['inputAnioSuperior']
			curricular_scope = request.form['inputCurricularScope']
			if not(nombre=="" or fecha_comienzo=="" or fecha_fin=="" or cicle=="" or curricular_scope =="" or establismentId==""):
				fecha_comienzo = datetime.datetime.strptime(fecha_comienzo, '%Y-%m-%d')
				fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d')
				if fecha_fin<fecha_comienzo:
					return render_template('course/new_course.html', dateError="La fecha de comienzo debe ser anterior a la de fin.", nombre=nombre, curricularScopes=curricularScopes, establishments=establishments)
				hoy = datetime.datetime.strptime(str(date.today()), '%Y-%m-%d')
				if fecha_comienzo<hoy:
					return render_template('course/new_course.html', dateError="La fecha de comienzo debe ser posterior a la fecha actual.", nombre=nombre, curricularScopes=curricularScopes, establishments=establishments)
				Course.create_course(nombre, fecha_comienzo, fecha_fin, session['id'], establismentId, cicle, year, curricular_scope)
				return redirect(url_for('courses'))
		return render_template('course/new_course.html', emptyField="Debe completar todos los campos.", curricularScopes=curricularScopes, establishments=establishments)
	return redirect(url_for('home'))

def view_course(course_id):
	if session['actualRole'] == "professor":

		course = Course.get_course(course_id)

		activities = Activity.get_activities_of_course(course_id)
		students = User.get_user_from_course(course_id)
		
		students_to_add = User.get_students_to_add(course_id, course['establishment_id'])
		

		establishmentId = course['establishment_id']

		datasetsToAdd = Dataset.get_datasets_to_add_to_course(session['id'], establishmentId, course_id)

		datasets = Course.get_dataset_by_courseId(course_id)

		return render_template('course/view_course.html', course=course, activities=activities, fecha_actual=date.today(), alumnos=students, datasetsToAdd=datasetsToAdd, datasets=datasets, students_to_add=students_to_add)
	return redirect(url_for('home'))

def invite_user_to_course(username, course_id):
	if session['actualRole'] == "professor":
		result = Course.invite_user_to_course(username,course_id)
		return jsonify(result = result)
	return redirect(url_for('home'))


def is_user_on_course(username, course_id):
	if session['actualRole'] == "professor":
		result = Course.is_user_on_course(username,course_id)
		return jsonify(result = result)
	return redirect(url_for('home'))

def course_add_dataset():
	if request.method=="POST":
		datasetId = request.form['dataset']
		courseId = request.form['courseId']

		Course.add_dataset(datasetId, courseId)

		flash('Dataset agregado correctamente', 'success')
		return view_course(courseId)
	return redirect(url_for('home'))

def get_curricular_scope():
	if session['actualRole'] == "professor":
		curricularScopes = Course.get_curricular_scope()
		return curricularScopes
	return redirect(url_for('home'))
