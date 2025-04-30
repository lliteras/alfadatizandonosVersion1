from flask import redirect, render_template, request, url_for, session, abort, flash
import psycopg2
import psycopg2.extras
from db import get_db, get_db_visualization

class Visualization(object):

	db = None

	@classmethod
	def get_database(cls, Bid):
		query = ("SELECT * FROM public.\"Database\" as d " +
				"WHERE d.id = "+str(Bid))
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchone()

	@classmethod
	def get_db_data(cls, Bid):
		query = ("SELECT C.name, C.type FROM public.\"Database\" as d inner join public.\"Database_table\" as dt on d.id = dt.id_database " +
				"inner join public.\"Table\" as t on dt.id_table = t.id " +
				"inner join public.\"Table_column\" as tc on t.id = tc.id_table " +
				"inner join public.\"Column\" as c on tc.id_column = c.id " +
				"WHERE t.fact_table = True AND d.id = "+str(Bid))
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()


	@classmethod
	def getColumnsOfObject(cls, databaseName, columnName):
		query = ("SELECT C.name, C.type FROM public.\"Table\" as t "+
				"inner join public.\"Table_column\" as tc on t.id = tc.id_table " +
				"inner join public.\"Column\" as c on tc.id_column = c.id " +
				"WHERE t.name = \'"+databaseName +"-"+columnName+"\'")
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()	


	@classmethod
	def get_data(cls, data_db_name, table, column_x, condition, innerColumnsCondition):
		query = ("SELECT t0." +column_x + ", COUNT(t.id) as count " +
				" FROM \"" + table + "\" as t "+ 
				"INNER JOIN \""+ data_db_name + "-" + column_x + "\" as t0_0 on (t.id = t0_0.id_"+data_db_name+") "+
				"INNER JOIN \""+ column_x + "\" as t0 on (t0_0.id_"+column_x+" = t0.id) "+
				innerColumnsCondition + " "+

				#"INNER JOIN " + "\""+ table + "-" + column_x + "\" as t0 on (t." + column_x + " = t0.id )" + innerColumnsCondition + " " +

				condition + 
				" GROUP BY t0." + column_x +" ORDER BY " + column_x + " ASC ")
		cursor = get_db_visualization(data_db_name).cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()

	@classmethod
	def getColumnData(cls, database, column, condition, pos):
		query = ("SELECT * FROM \"" + column + "\" as t"+str(pos)+" " + condition)
		cursor = get_db_visualization(database).cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()

	@classmethod	
	def get_data_for_data_table(cls, data_db_name, row, column, condition, innerColumnsCondition, counts):
		query = ("SELECT t0." +row + ", "+ counts +
				" FROM \"" + data_db_name + "\" as t "+
				#" INNER JOIN " + "\""+ data_db_name + "-" + row + "\" as t0 on (t." + row + " = t0.id ) " + 
				"INNER JOIN \""+ data_db_name + "-" + row + "\" as t0_0 on (t.id = t0_0.id_"+data_db_name+") "+
				"INNER JOIN \""+ row + "\" as t0 on (t0_0.id_"+row+" = t0.id) "+
				"INNER JOIN \""+ data_db_name + "-" + column + "\" as t1_1 on (t.id = t1_1.id_"+data_db_name+") "+
				"INNER JOIN \""+ column + "\" as t1 on (t1_1.id_"+column+" = t1.id) "+
				#" INNER JOIN \""+ data_db_name + "-" + column + "\" as t1 on (t."+column+" = t1.id) "+
				
				innerColumnsCondition + " " +
				condition + 
				" GROUP BY t0." + row +" ORDER BY " + row + " ASC ")
		cursor = get_db_visualization(data_db_name).cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()	

	@classmethod	
	def get_data_for_data_table_without_column(cls, data_db_name, row, condition, innerColumnsCondition, counts):
		query = ("SELECT t0." +row + ", "+ counts +
				" FROM \"" + data_db_name + "\" as t "+
				#" INNER JOIN " + "\""+ data_db_name + "-" + row + "\" as t0 on (t." + row + " = t0.id ) " + 
				"INNER JOIN \""+ data_db_name + "-" + row + "\" as t0_0 on (t.id = t0_0.id_"+data_db_name+") "+
				"INNER JOIN \""+ row + "\" as t0 on (t0_0.id_"+row+" = t0.id) "+
				innerColumnsCondition + " " +
				condition + 
				" GROUP BY t0." + row +" ORDER BY " + row + " ASC ")
		cursor = get_db_visualization(data_db_name).cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()	

	@classmethod
	def get_data_with_parameters(cls, data_db_name, selectString, fromString, groupByString, whereString):
		query = ("SELECT "+selectString+ " FROM "+ fromString +
		" "+whereString+ 
		"GROUP BY " +groupByString+ " ORDER BY " + groupByString + " ASC " )
		cursor = get_db_visualization(data_db_name).cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)


		return cursor.fetchall()	

	@classmethod
	def get_data_with_parameters_for_scatter(cls, data_db_name, selectString, fromString, orderByString, whereString):
		query = ("SELECT "+selectString+ " FROM "+ fromString +
		" "+whereString+ 
		" ORDER BY " + orderByString + " ASC " )
		cursor = get_db_visualization(data_db_name).cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)


		return cursor.fetchall()

	@classmethod
	def get_data_with_parameters_for_inspection(cls, data_db_name, selectString, fromString, whereString):
		query = ("SELECT "+selectString+ " FROM "+ fromString +
		" "+whereString+ " LIMIT 1000 " )
		cursor = get_db_visualization(data_db_name).cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)


		return cursor.fetchall()			

	@classmethod	
	def get_database_id(cls, data_db_name):
		query = ("SELECT * FROM public.\"Database\" as d " +
				"WHERE d.name = '"+data_db_name+"'")
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchone()