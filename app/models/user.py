from flask import redirect, render_template, request, url_for, session, abort, flash
import psycopg2
import psycopg2.extras
from db import get_db

class User(object):

	db = None

	@classmethod
	def get_all_users(cls):
		query = "SELECT * FROM public.user"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()

	@classmethod
	def get_all_users_with_pagination(cls, pagination, actual_page, filtered):
		query = "SELECT u.id, u.name, u.surname, u.email, u.username FROM public.user as u "
		params = ()
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)

		if filtered != 0:
			query = query + "INNER JOIN user_role ON u.id = user_role.user_id WHERE user_role.role_id = %s "
			params = params + (filtered,)
		cursor.execute(query, (params))
		
		rowsCount = cursor.rowcount

		maxPage = ((rowsCount-1)//pagination)+1
		start_at = (actual_page-1)*pagination

		query = query + "LIMIT %s OFFSET %s"
		params = params + (pagination, start_at,)
		cursor.execute(query, (params))
		return [cursor.fetchall(), maxPage]

	@classmethod
	def login(cls, user, email):
		query= "SELECT * FROM public.user as u INNER JOIN user_role ON user_role.user_id = id INNER JOIN role ON role.id = user_role.role_id WHERE (username=%s OR email=%s)"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (user, email))

		return cursor.fetchall()

	@classmethod
	def register(cls, username, password, province, city, institute, email, name, surname, birthday):
		con = get_db()

		query="INSERT INTO public.user(username, password, province_id, city_id, email, name, surname, birthday) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (username, password, province, city, email, name, surname, birthday))
		a = cursor.fetchone()[0]
		query="INSERT INTO public.user_role VALUES(%s, '3')"
		cursor.execute(query, (a,))
		query="INSERT INTO public.user_establishment VALUES(%s,%s)"
		cursor.execute(query, (a,institute))
		con.commit()

		return True
	

	@classmethod
	def emailExist(cls, email):

		query = "SELECT * FROM public.user WHERE email=%s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (email,))

		if cursor.fetchone():
			return True
		else: 
			return False

	@classmethod
	def usernameExist(cls, username):
		query = "SELECT * FROM public.user WHERE username=%s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (username,))

		if cursor.fetchone():
			return True
		else: 
			return False

	@classmethod
	def get_user_from_course(cls, course_id):

		query = "SELECT * FROM public.user as u INNER JOIN user_course ON user_course.user_id = u.id WHERE user_course.course_id = %s ORDER BY surname asc"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (course_id,))

		return cursor.fetchall()

	@classmethod
	def get_roles_of_user(cls, user_id):
		query = "SELECT role_id FROM public.user_role WHERE user_id = %s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (user_id,))

		return cursor.fetchall()

	@classmethod
	def user_or_email_exist(cls, username):
		query = "SELECT * FROM public.user WHERE email=%s or username=%s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (username, username))

		return cursor.fetchone()

	@classmethod
	def get_user_by_id(cls, id_user):
		query = "SELECT * FROM public.user WHERE id=%s"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (id_user,))

		return cursor.fetchone()

	@classmethod
	def get_information_of_user(cls, id_user):
		query = "SELECT u.id, name, email, surname, birthday, username, localidad, jurisdiccion FROM public.user u INNER JOIN city c ON c.id = u.city_id INNER JOIN province p ON p.id = u.province_id  WHERE u.id=%s "
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (id_user,))

		return cursor.fetchone()

	@classmethod
	def get_establishments_of_user(cls,id_user):
		query = "SELECT localidad, codigo_de_area, jurisdiccion, cue, nombre, ambito, domicilio, telefono, mail, e.id as establishment_id FROM public.user_establishment u INNER JOIN establishment e ON e.id = u.id_establishment INNER JOIN city c ON c.id = e.id_ciudad::integer INNER JOIN province p ON p.id = c.id_provincia::integer  WHERE u.id_user=%s ORDER BY nombre"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (id_user,))

		return cursor.fetchall()

	@classmethod
	def add_institute(cls, id_user, id_establishment):
		con = get_db()
		query = "INSERT INTO public.user_establishment VALUES(%s,%s)"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (id_user,id_establishment))
		con.commit()
		return True

	@classmethod
	def get_students_to_add(cls, id_course, id_establishment):
		query = "SELECT * FROM public.user u INNER JOIN user_establishment ON u.id = user_establishment.id_user WHERE id_establishment = %s AND u.id NOT IN (SELECT user_id FROM user_course WHERE course_id=%s)"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (id_establishment,id_course))

		return cursor.fetchall()