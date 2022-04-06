import psycopg2
from flask import current_app, g
from flask.cli import with_appcontext
import config

def get_db():

	g.db = psycopg2.connect(
		host = config.DB_HOST,
		user = config.DB_USER,
		password = config.DB_PASS,
		dbname = config.DB_NAME
		)
	return g.db	

def get_db_visualization(data_db_name):
	
	g.db = psycopg2.connect(
		host = config.DB_HOST,
		user = config.DB_USER,
		password = config.DB_PASS,
		dbname = data_db_name
		)

	return g.db	
