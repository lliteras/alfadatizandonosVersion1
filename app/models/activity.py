from flask import redirect, render_template, request, url_for, session, abort, flash
import psycopg2
import psycopg2.extras
from db import get_db

class Activity(object):

	db = None

	@classmethod
	def getMyActivities(cls, user_id):
		query = ("SELECT a.id, a.start_date, a.end_date, title, has_calification, enable_expired_date, calification, user_activity.commentary, is_finished, name as course_name, Max(date_resolution) "+
			" FROM public.activity as a "+
			" INNER JOIN user_activity ON user_activity.id_activity = a.id "+
			" INNER JOIN course ON a.course_id= course.id "+
			" LEFT JOIN user_activity_resolution as uar ON (uar.id_activity = user_activity.id_activity  AND  uar.id_user = user_activity.id_user  ) "+
			" WHERE user_activity.id_user=%s "+
			" GROUP BY a.id, a.start_date, a.end_date, title, has_calification, enable_expired_date, calification, user_activity.commentary, is_finished, name"+
			" ORDER BY a.end_date desc")
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute(query, (user_id,))
		return cursor.fetchall()



	@classmethod
	def create_activity(cls, start_date, end_date, title, description, course_id, graphs, objective, has_calification, enable_expired_date, statement_title, statement, students, datasetId, socialGraph):
		con = get_db()
		query = "INSERT INTO public.activity(start_date, end_date, title, description, course_id, objective, has_calification, enable_expired_date,statement_title, statement, dataset_id, social_graph) VALUES(%s,%s,%s,%s,%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (start_date, end_date, title, description, course_id, objective, has_calification, enable_expired_date, statement_title, statement, str(datasetId), str(socialGraph)))
		a = cursor.fetchone()[0]
		query = "INSERT INTO public.activity_available_graph VALUES(%s, %s)"
		var = []
		for graph in graphs:
			var.append((a,graph))
		cursor.executemany(query, var)
		query3 = "INSERT INTO public.user_activity(id_user, id_activity) VALUES(%s, %s)"
		var2 = []
		for student in students:
			var2.append((student, a))
		cursor.executemany(query3, var2)
		con.commit()
		return True


	@classmethod 
	def get_graph_names(cls):
		query = "SELECT id, spanish_name FROM public.\"Graph\""
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()

	@classmethod
	def get_activities_of_course(cls, course_id):
		query = "SELECT * FROM activity WHERE course_id=%s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (course_id,))

		return cursor.fetchall()

	@classmethod
	def get_activity_by_id(cls, activity_id):
		query = "SELECT * FROM activity WHERE id=%s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (activity_id,))

		return cursor.fetchone()

	@classmethod
	def get_graph_of_activity_by_id(cls, activity_id):
		query = "SELECT * FROM public.activity_available_graph as aag INNER JOIN public.\"Graph\" as g on aag.graph_id = g.id WHERE aag.activity_id=%s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (str(activity_id),))

		return cursor.fetchall()

	@classmethod

	def inset_resolution(cls, activityId, userId, resolutionType, dateTimeNow ,commentary):

		con = get_db()

		query = "INSERT INTO public.user_activity_resolution(id_user, id_activity, date_resolution, resolution_type, commentary) VALUES(%s,%s,%s,%s,%s) RETURNING id_resolution;"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (str(userId), str(activityId), str(dateTimeNow), resolutionType, commentary))

		con.commit()

		return cursor.fetchone()[0]

	@classmethod
	def insert_resolution_plotter(cls, plotterResolutionFields, plotterResolutionFieldsValues):

		con = get_db()

		query = "INSERT INTO public.resolution_plotter("+plotterResolutionFields+") VALUES( "+plotterResolutionFieldsValues+") RETURNING id_resolution_plotter;"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		con.commit()



		return cursor.fetchone()[0]

	@classmethod
	def insert_resolution_plotter_conditions(cls, stringConditions, resolution_plotter_id):

		con = get_db()

		query = "INSERT INTO public.resolution_plotter_conditions(id_resolution_plotter, condition) VALUES(%s, %s)"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		var = []
		for condition in stringConditions.split(sep='~~~'):
			var.append((str(resolution_plotter_id), condition))
		cursor.executemany(query, var)

		con.commit()

		return None

	@classmethod
	def insert_resolution_social_graph(cls, resolution_id, searchString, excludePrepositions, excludeArticles, excludePronouns, excludeConjunctions, excludeAdverbs, excludeVerbs, excludeLinks, quantityOfWords, cloudBase64, plotterBase64):	

		con = get_db()

		query = "INSERT INTO public.resolution_social_graph(id_resolution, phrase_to_search, exclude_prepositions, exclude_articles, exclude_pronouns, exclude_conjunctions, exclude_adverbs, exclude_verbs, exclude_links, quantity_of_words, cloud_image, plotter_image) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (str(resolution_id), searchString, str(excludePrepositions), str(excludeArticles), str(excludePronouns), str(excludeConjunctions), str(excludeAdverbs), str(excludeVerbs), str(excludeLinks), str(quantityOfWords), str(cloudBase64), str(plotterBase64) ))

		con.commit()

		return None


	@classmethod
	def get_user_activity_resolution(cls, userId, activityId):

		query = "SELECT * FROM public.user_activity_resolution as uas WHERE id_activity =%s AND id_user = %s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (str(activityId),str(userId)))

		return cursor.fetchall()

	@classmethod
	def get_students_from_activity(cls, activity_id):
		query = ("SELECT u.id, u.name, u.surname, ua.calification, Max(uac.date_resolution) as date_resolution FROM public.user u INNER JOIN user_activity ua ON u.id = ua.id_user LEFT JOIN public.user_activity_resolution as uac on (uac.id_activity = ua.id_activity AND uac.id_user = u.id)" +
				" WHERE ua.id_activity=%s"+
				" GROUP BY u.id, u.name, u.surname, ua.calification ")
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (str(activity_id),))

		return cursor.fetchall()

	@classmethod
	def get_resolution(cls, resolution_id):

		query = "SELECT * FROM public.user_activity_resolution as ar WHERE id_resolution =%s "
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (str(resolution_id),))

		return cursor.fetchone()


	@classmethod
	def get_activity_of_student(cls,activity_id, user_id):
		query = "SELECT * FROM public.user_activity INNER JOIN public.user u ON u.id = user_activity.id_user WHERE id_activity=%s and id_user=%s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (activity_id,user_id))

		return cursor.fetchone()

	@classmethod
	def get_plotter_resolution(cls,resolution_id):
		query = "SELECT * FROM public.resolution_plotter as rp WHERE id_resolution =%s "
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute(query, (str(resolution_id),))

		return cursor.fetchone()

	@classmethod
	def get_plotter_resolution_conditions(cls,plotter_resolution_id):
		query = "SELECT * FROM public.resolution_plotter_conditions as uac WHERE id_resolution_plotter =%s "
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute(query, (str(plotter_resolution_id),))

		return cursor.fetchall()	

	@classmethod
	def get_social_graph_resolution(cls, resolution_id):

		query = "SELECT * FROM public.resolution_social_graph as rp WHERE id_resolution =%s "
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.RealDictCursor)
		cursor.execute(query, (str(resolution_id),))

		return cursor.fetchone()


	@classmethod
	def correct_activity(cls, activity_id, user_id, calification, commentary):
		con = get_db()
		query = "UPDATE user_activity SET calification=%s, commentary=%s WHERE id_activity=%s and id_user=%s"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (calification, commentary, activity_id,user_id))
		con.commit()

		return True
