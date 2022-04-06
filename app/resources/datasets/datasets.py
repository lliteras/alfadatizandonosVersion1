from flask import redirect, render_template, request, url_for, session, abort, flash
from models.dataset import Dataset
from models.visualization import Visualization
from models.user import User


pagination = 10

def datasets():

	return render_template('datasets/datasets.html')	

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


def indexPublics(page, condition):

	if session['id']:

		stringCondtion= ''

		if condition:

			stringCondtion = 'AND LOWER(d.name) LIKE LOWER(\'%'+condition+'%\')'

		datasets = Dataset.get_dataset_public(page, pagination, stringCondtion)

		maxPage = Dataset.max_page_publics(pagination, stringCondtion)

		availablePages = getAvailablePages(page, maxPage)
		
		return render_template('datasets/index.html', datasets=datasets, nombre='Públicos', name='publics', availablePages=availablePages, maxPage=maxPage, actualPage=page, condition=condition)	

	else: 

		flash('Debe estar logeado para realizar esta accion', 'danger')

		return redirect(url_for('loginForm'))		

def indexProtecteds(page, condition):

	if session['id']:

		stringCondtion= ''

		if condition:

			stringCondtion = 'AND LOWER(d.name) LIKE LOWER(\'%'+condition+'%\')'

		datasets = Dataset.get_dataset_protected(session['id'], page, pagination, stringCondtion)

		maxPage = Dataset.max_page_protecteds(pagination, session['id'], stringCondtion)

		availablePages = getAvailablePages(page, maxPage)
		
		return render_template('datasets/index.html', datasets=datasets, nombre='protegidos', name='protecteds', availablePages=availablePages, maxPage=maxPage, actualPage=page, condition=condition)

	else:

		flash('Debe estar logeado para realizar esta accion', 'danger')

		return redirect(url_for('loginForm'))


def indexPrivates(page, condition):

	if session['id']:

		stringCondtion= ''

		if condition:

			stringCondtion = 'AND LOWER(d.name) LIKE LOWER(\'%'+condition+'%\')'

		datasets = Dataset.get_dataset_privates(session['id'], page, pagination, stringCondtion)

		maxPage = Dataset.max_page_privates(pagination, session['id'], stringCondtion)

		availablePages = getAvailablePages(page, maxPage)
		
		return render_template('datasets/index.html', datasets=datasets, nombre='privados', name='privates', availablePages=availablePages, maxPage=maxPage, actualPage=page, condition=condition)			
	
	else:

		flash('Debe estar logeado para realizar esta accion', 'danger')

		return redirect(url_for('loginForm'))		

def show(Bid):	

	if session['id']:

		if checkSessionCanAccess(Bid):

			sessionId= session['id']

			#get the columns of the database
			columns = Visualization.get_db_data(Bid)

			#get the database
			database = Dataset.get_dataset_with_owner(Bid)

			canEdit = sessionId == database['database_owner_id']

			establisments = User.get_establishments_of_user(database['database_owner_id'])

			#get the structure of the dataset
			databaseStructure = {}

			for column in columns:
				if column['type'] == 'object': 

					dictionaryObject = {}

					columnsOfObject = Visualization.getColumnsOfObject(database['name'],column['name'])

					for columnOfObject in columnsOfObject:
						if columnOfObject['type'] == 'object':

							dictionaryObject[columnOfObject['name']] = generateStructureRecursion(database['name'], column['name'], columnOfObject['name'])

						else:  

							dictionaryObject[columnOfObject['name']] = columnOfObject['type'] 

					databaseStructure[column['name']] = dictionaryObject        

				else: 
					databaseStructure[column['name']] = column['type'] 

			return render_template('datasets/show.html', columns = columns, database = database, databaseStructure = databaseStructure, canEdit = canEdit, establisments=establisments)

	else:

		flash('Debe estar logeado para realizar esta accion', 'danger')

		return redirect(url_for('loginForm'))				



def generateStructureRecursion(databaseName, columnName, columnNameOfObject): 

    dictionaryObject = {}

    columnsOfObject = Visualization.getColumnsOfObject(databaseName,columnName+'-'+columnNameOfObject)

    for columnOfObject in columnsOfObject:
        if columnOfObject['type'] == 'object':

            dictionaryObject[columnOfObject['name']] = generateStructureRecursion(databaseName, columnNameOfObject, columnOfObject['name'])

        else:    
            dictionaryObject[columnOfObject['name']] = columnOfObject['type'] 

    return dictionaryObject  

def checkSessionCanAccess(Bid):

	establishmentId = (User.get_user_by_id(session['id']))['establishment_id']
	
	return Dataset.check_can_access_to_dataset(Bid, session['id'], establishmentId)

def editShare():

	if session['id']:

		if ((request.form.get('id')) and (request.form.get('share'))):

			datasetId = request.form['id']
			datasetShare = request.form['share']

			Dataset.dataset_edit_share(datasetId, datasetShare)

			#establishmentId = (User.get_user_by_id(session['id']))['establishment_id']

			if datasetShare == 'protegido':

				establishments = request.form.getlist('establisment')
				
				Dataset.add_dataset_to_stablisment(datasetId, establishments)
			else:	

				Dataset.delete_dataset_from_stablisment(datasetId)


			return redirect('/datasets/show/'+datasetId)

		else:

			flash('Lo sentimos, el formulario no se ha enviado correctamente', 'danger')

			return redirect('/datasets/show/'+datasetId)
		


	else:

		flash('Debe estar logeado para realizar esta accion', 'danger')

		return redirect(url_for('loginForm'))		



        