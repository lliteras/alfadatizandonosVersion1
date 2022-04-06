import psycopg2
import psycopg2.extras
from db import get_db

class Dataset(object):

	db = None

	@classmethod
	def get_dataset_public(cls, page, pagination, stringCondtion):
		start_at = (page-1)*pagination

		query = ("SELECT d.id, d.name as dataset_name, u.name, u.surname FROM public.\"Database\" as d  INNER JOIN public.\"user\" as u on d.database_owner_id = u.id " + 
				"WHERE d.share = 'publico' "+stringCondtion +" ORDER BY d.name limit "+str(pagination)+ " OFFSET " +str(start_at)  )

		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()

	@classmethod
	def max_page_publics(cls, pagination, stringCondtion):
		query = ("SELECT d.id, d.name as dataset_name, u.name, u.surname FROM public.\"Database\" as d  INNER JOIN public.\"user\" as u on d.database_owner_id = u.id " + 
				"WHERE d.share = 'publico' "+stringCondtion +""  )
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		rowsCount = cursor.rowcount

		maxPage = ((rowsCount-1)//pagination)+1

		return maxPage
				
	

	@classmethod
	def get_dataset(cls, Bid):
		query = ("SELECT * FROM public.\"Database\" as d " +
				"WHERE d.id = "+str(Bid))
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchone()	

	@classmethod
	def get_dataset_with_owner(cls, Bid):
		query = ("SELECT d.id, d.name, d.database_owner_id, d.share, u.name as user_name, u.surname FROM public.\"Database\" as d INNER JOIN public.\"user\" as u on d.database_owner_id = u.id " +
				"WHERE d.id = "+str(Bid))
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchone()	
	

	@classmethod
	def dataset_edit_share(cls, Bid, share):
		
		con = get_db()

		query = ("UPDATE public.\"Database\" SET share = '"+ share +
				"' WHERE id = "+str(Bid))
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		con.commit()

		return None		

	@classmethod
	def add_dataset_to_stablisment(cls,  datasetId, establishmentsId):
		
		con = get_db()

		query = ("INSERT INTO public.\"Dataset_establishment\" (id_dataset, id_establishment) VALUES ( (%s)::integer, (%s)::integer )")
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		var = []
		for establishmentId in establishmentsId:
			var.append((datasetId, establishmentId))
		cursor.executemany(query, var)

		con.commit()

		return True

	@classmethod
	def delete_dataset_from_stablisment(cls, Bid):

		con = get_db()

		query = ("DELETE FROM public.\"Dataset_establishment\" WHERE id_dataset = %s")
		cursor = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query, (str(Bid),))

		con.commit()	

	@classmethod
	def get_datasets_to_add_to_course(cls, user_id, establishment_id, course_id):

		query = ("SELECT d.id, d.name as dataset_name FROM public.\"Database\" as d " + 
				"WHERE d.share = 'publico' OR "+
				"(d.share = 'protegido' AND d.id IN (SELECT id_dataset from public.\"Dataset_establishment\" where id_establishment = "+str(establishment_id)+"   ) ) "+ 
				"OR d.database_owner_id = "+str(user_id)+" AND "+
				"d.id NOT IN (select id_dataset from public.\"Dataset_course\" where id_course = "+str(course_id)+" ) ")

		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()	

	@classmethod
	def get_dataset_protected(cls, user_id, page, pagination, stringCondtion):

		start_at = (page-1)*pagination

		query = ("SELECT DISTINCT d.id, d.name as dataset_name, u.name, u.surname FROM public.\"Database\" as d INNER JOIN public.\"user\" as u on d.database_owner_id = u.id INNER JOIN user_establishment ue on ue.id_user	=u.id " +
				"WHERE "+
				"d.id IN (SELECT id_dataset from public.\"Dataset_establishment\" where id_establishment = ue.id_establishment)  "+ 
				"OR d.id IN (select id_dataset from public.\"Dataset_course\" as dc INNER JOIN public.\"user_course\" as uc on dc.id_course = uc.course_id where uc.user_id = "+str(user_id)+" ) "+stringCondtion +" "+
				"ORDER BY d.name limit "+str(pagination)+ " OFFSET " +str(start_at))

		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()	

	@classmethod
	def max_page_protecteds(cls, pagination, user_id, stringCondtion):
		query = ("SELECT d.id, d.name as dataset_name, u.name, u.surname FROM public.\"Database\" as d INNER JOIN public.\"user\" as u on d.database_owner_id = u.id INNER JOIN user_establishment ue on ue.id_user	=u.id " +
				"WHERE "+
				"d.id IN (SELECT id_dataset from public.\"Dataset_establishment\" where id_establishment = ue.id_establishment)  "+ 
				"OR d.id IN (select id_dataset from public.\"Dataset_course\" as dc INNER JOIN public.\"user_course\" as uc on dc.id_course = uc.course_id where uc.user_id = "+str(user_id)+" ) "+stringCondtion)

		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		rowsCount = cursor.rowcount

		maxPage = ((rowsCount-1)//pagination)+1

		return maxPage
					

	@classmethod
	def get_dataset_privates(cls, user_id, page, pagination, stringCondtion):

		start_at = (page-1)*pagination

		query = ("SELECT d.id, d.name as dataset_name, u.name, u.surname FROM public.\"Database\" as d INNER JOIN public.\"user\" as u on d.database_owner_id = u.id " +
				"WHERE d.database_owner_id = "+str(user_id)+" "+stringCondtion +" "
				" ORDER BY d.name limit "+str(pagination)+ " OFFSET " +str(start_at))
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return cursor.fetchall()	

	@classmethod
	def max_page_privates(cls, pagination, user_id, stringCondtion):
		query = ("SELECT d.id, d.name as dataset_name, u.name, u.surname FROM public.\"Database\" as d INNER JOIN public.\"user\" as u on d.database_owner_id = u.id " +
				"WHERE d.database_owner_id = "+str(user_id))+" "+stringCondtion +" "
		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		rowsCount = cursor.rowcount

		maxPage = ((rowsCount-1)//pagination)+1

		return maxPage
						

	@classmethod
	def check_can_access_to_dataset(cls, dataset_id, user_id, establishment_id):
		
		query = ("SELECT d.id, d.name as dataset_name FROM public.\"Database\" as d INNER JOIN public.\"user\" as u on d.database_owner_id = u.id " +
				"WHERE d.id = "+str(dataset_id)+" AND( "+
				"d.share = 'publico' OR " + 
				" d.database_owner_id = "+str(user_id)+" OR " +
				"u.establishment_id = "+str(establishment_id)+"  "+ 
				"OR d.id IN (select id_dataset from public.\"Dataset_course\" as dc INNER JOIN public.\"user_course\" as uc on dc.id_course = uc.course_id where uc.user_id = "+str(user_id)+" )) ")

		cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
		cursor.execute(query)

		return (len(cursor.fetchall()) > 0)			

