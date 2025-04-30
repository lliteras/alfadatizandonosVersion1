from flask import redirect, render_template, request, url_for, session, abort, flash
import psycopg2
import psycopg2.extras
from datetime import date
from db import get_db

class Configuration(object):

	db = None

	@classmethod
	def add_file_data(cls, filename):

		con = get_db()

		query = "UPDATE public.configuration SET establishment_filename = \'" + filename  + "\', establishment_update_day=\'" + str(date.today()) + "\'"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)
		con.commit()

		return True

	@classmethod
	def get_file_data(cls):
		query = "SELECT * FROM public.configuration"
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchone()

	@classmethod
	def change_role(cls,user_id, role_id):
		con = get_db()
		query = "UPDATE public.user as u SET role_id = \'" + role_id + "\' WHERE u.id = \'" + user_id  + "\'"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)
		con.commit()

	@classmethod
	def delete_role(cls, user_id, role_id):
		con = get_db()
		query = "DELETE FROM public.user_role WHERE user_id=%s and role_id=%s"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (user_id, role_id))
		con.commit()
		return None

	@classmethod
	def add_role(cls, user_id, role_id):
		con = get_db()
		query = "INSERT INTO public.user_role VALUES(%s,%s)"
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (user_id, role_id))
		con.commit()
		return None
