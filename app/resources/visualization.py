from flask import redirect, render_template, request, url_for, session, abort, flash, jsonify
from datetime import datetime 
from bokeh.plotting import figure, output_file, show
from bokeh.models.tools import HoverTool
import pandas as pd
from bokeh.models import ColumnDataSource, Div, Select, Slider, TextInput, Range1d, OpenURL, TapTool
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.io import curdoc
from bokeh.resources import INLINE
from bokeh.embed import components
from models.visualization import Visualization
from models.activity import Activity
from math import pi
import numpy as np
from bokeh.transform import cumsum, jitter
from bokeh.palettes import Category20, cividis, Set3, Set1, Category10
from bokeh.tile_providers import CARTODBPOSITRON, get_provider


#return the plotter page
def plotter(Bid, activityId):

    if session['id']:

        graphs = []
        noNav = False

        if activityId:

            graphs = Activity.get_graph_of_activity_by_id(activityId)
            graphs = [ x['name'] for x in graphs]

            noNav = True

        else:
        
            graphs = ['data_table','bar','line','pie','dot','scatter','map'] 

        #get the columns of the database
        columns = Visualization.get_db_data(Bid)
        
        #get the database
        database = Visualization.get_database(Bid)

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


                #databaseStructure[column['name']] = generateStructureRecursion(database['name'],)

            else:    
                databaseStructure[column['name']] = column['type'] 



        return render_template('home/plotter.html', columns = columns, database= database, databaseStructure = databaseStructure, graphs=graphs, noNav=noNav)  

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


def queryConstruction(database, rowName, column, condition):
    
    dictPositionsInQuery = {}

    columnsToAddToDict = rowName.split(sep='***')
    columnsToAddToDict.append('object')

    aux = addPosInQuery(columnsToAddToDict, dictPositionsInQuery, 0)

    dictPositionsInQuery = aux[0]
    topPos = aux[1]

    columnToGroupBy = ''

    if column != 'undefined':

        columnsToAddToDict = column.split(sep='***')
        columnsToAddToDict.append('object')

        aux = addPosInQuery(columnsToAddToDict, dictPositionsInQuery, topPos)

        dictPositionsInQuery = aux[0]
        topPos = aux[1]

        columnsToAddToDict = column.split(sep='***')
        columnsToAddToDict.append('object')

        valueColumnGroupBy = columnsToAddToDict[len(columnsToAddToDict)-2] 
        posGroupBy = positionInQuery(columnsToAddToDict, dictPositionsInQuery)
        columnToGroupBy = ', t'+str(posGroupBy)+'.'+valueColumnGroupBy

    conditionQueryString = ''
    
    if condition != None:
        for cond in condition.split(sep='~~~'):
            
            if cond.find('like \'%') == -1:

                #get the name of the column (first part of the condition)
                columnCondition = cond.split(sep='=')[0]
                
                columnCondition = columnCondition[:-1].strip()
            
            else:       

                columnCondition = cond.split(sep='like \'%')[0].strip()

                

            columnsToAddToDict = columnCondition.split(sep='***')
            columnsToAddToDict.append('object')

            aux = addPosInQuery(columnsToAddToDict, dictPositionsInQuery, topPos)   

            dictPositionsInQuery = aux[0]
            topPos = aux[1]
        
        #call the method to transform the conditions
        conditionQueryString = conditionsToString(database, condition, dictPositionsInQuery)        

    fromOfQueryString = 'public.\"'+ database + '\" as t0 '

    fromOfQueryString = generateSelect(dictPositionsInQuery[database], fromOfQueryString , database, database)     

    columnsToAddToDict = rowName.split(sep='***')
    columnsToAddToDict.append('object')

    valueColumn = columnsToAddToDict[len(columnsToAddToDict)-2] 
    pos = positionInQuery(columnsToAddToDict, dictPositionsInQuery)

    groupByString = 't'+str(pos)+'.\"'+valueColumn+'\"'
    selectString = groupByString + ',  COUNT( t'+str(pos)+'.id) as count'
    #selectString = 't'+str(pos)+'.\"'+valueColumn + '\",  COUNT( t'+str(pos)+'.id) as count'

    return {'groupByString':groupByString, 'selectString':selectString, 'fromOfQueryString':fromOfQueryString, 'pos':pos, 'valueColumn':valueColumn, 'whereString':conditionQueryString, 'dictPositionsInQuery':dictPositionsInQuery, 'columnToGroupBy':columnToGroupBy}

#transform the string of conditions to the format that the query needs
def conditionsToString(database, condition, dictPositionsInQuery):    

    #array of the columns that will need the query to have the columns of the conditions
    columnsToInner = []
    # string of the inner joins
    innerColumnsCondition = ''
    
    #string of the conditions that will use the query
    queryCondition = ''

    #dictionary of conditions positive
    queryConditionPositive = {}

    #string of negative conditions
    queryConditionNegative = '' 

    #check if there is a condition to transform
    if condition != None:
        
        #loop through the conditions. The conditions in the string are divided by '~~~'
        for cond in condition.split(sep='~~~'):
            
            #string condition 
            columnCondition = ''

            #check if the condition is not negative
            if cond.find('!=') == -1:       

                if cond.find('like \'%') == -1:                                                    
                
                    #get the name of the column (first part of the condition)
                    columnCondition = cond.split(sep='=')[0].strip()
                    
                    #check if the condition is 'mayor que' or 'menor que'
                    if columnCondition[-1] == '>' or columnCondition[-1] == '<':
                        
                        #if the condition is 'mayor que' or 'menor que' delete the white space and the '<' or '>'
                        columnCondition = columnCondition[:-2]    

                else:
                    
                    columnCondition = cond.split(sep='like \'%')[0].strip()       


                columnsToAddToDict = columnCondition.split(sep='***')

                valueColumn = 'id'

                

                if columnCondition != database:

                    columnsToAddToDict.append('object')

                    valueColumn = columnsToAddToDict[len(columnsToAddToDict)-2] 

                
                pos = positionInQuery(columnsToAddToDict, dictPositionsInQuery)

                condition = cond.replace(columnCondition, ' t'+str(pos)+'.\"'+valueColumn+'\" ')

                #If the 'valueColumn' not in 'QueryConditionPositive' it means that, have to create the array of that column
                if valueColumn not in queryConditionPositive:
                    
                    #create the array
                    queryConditionPositive[valueColumn] = []    

                #add the condition to the corresponding array
                queryConditionPositive[valueColumn].append(condition)                    


            #it means that the condition is negative
            else:

                #get the name of the column (first part of the condition)
                columnCondition = cond.split(sep='!=')[0].strip()

                

                columnsToAddToDict = columnCondition.split(sep='***')
                columnsToAddToDict.append('object')

                valueColumn = columnsToAddToDict[len(columnsToAddToDict)-2]          
                pos = positionInQuery(columnsToAddToDict, dictPositionsInQuery)

                condition = cond.replace(columnCondition, ' t'+str(pos)+'.\"'+valueColumn+'\" ')


                #if the string of negative condition is not empty add " AND " to separate the conditions
                if queryConditionNegative != '':
                    queryConditionNegative = queryConditionNegative + " AND "

                #Add the condition
                queryConditionNegative = queryConditionNegative + condition

        #add the negative part of conditions
        #if there is no negative conditions just add a '(False)'
        if not queryConditionNegative:
            queryCondition = "where (False) OR"

        #else, add the QueryConditionNegative
        else:
            queryCondition = "where (" +queryConditionNegative+ ") OR "                

        #add the positive part of conditions
        #if there is no positive conditions just add a '(False)'    
        if not queryConditionPositive:            
            queryCondition = queryCondition + " (False) "

        #else, add the positive condition
        else:

            #the positive condition is divided by 'OR' in the same column and by 'AND' in the diferent columns 
            for key in queryConditionPositive:
                queryCondition = queryCondition + '('

                for conditionpositive in queryConditionPositive[key]:
                    queryCondition = queryCondition + conditionpositive + ' OR '

                queryCondition = queryCondition[:-3] + ') AND '

            #delete the last 'AND ' of the string
            queryCondition = queryCondition[:-4]        

    #return the query condition and the inner joins
    return queryCondition       

 
def addPosInQuery(columns, dictPos, topPos):

    popped = columns.pop(0)

    if popped not in dictPos:
        
        dictPos[popped] = { 'pos' : topPos}
        topPos = topPos + 1             

    if columns:
        aux = addPosInQuery(columns, dictPos[popped], topPos)
        dictPos[popped] = aux[0]
        topPos = aux[1]

    return [dictPos, topPos]


def generateSelect(dictPositionsInQuery, fromOfQueryString, parentOfParentName, parentName):

    for key in dictPositionsInQuery.keys():

        if key != 'pos':

            if dictPositionsInQuery['pos'] == 0:

                onString = ' on t0.id = t'+str(dictPositionsInQuery[key]['pos'])+'.id_'+parentName
            
            else:

                if key == 'object':

                    onString = ' on t'+str(dictPositionsInQuery['pos'])+'.id_'+parentName+' = t'+str(dictPositionsInQuery[key]['pos'])+'.id'

                else:

                    onString = ' on t'+str(dictPositionsInQuery['pos'])+'.id_'+parentName+' = t'+str(dictPositionsInQuery[key]['pos'])+'.id_'+parentName


            if len(dictPositionsInQuery[key].keys()) > 1:

                fromOfQueryString = fromOfQueryString + ' INNER JOIN public.\"' + parentName+ '-'+ key + '\" as t'+ str(dictPositionsInQuery[key]['pos'])+ onString
                fromOfQueryString = generateSelect(dictPositionsInQuery[key], fromOfQueryString, parentName, key)

            else:

                fromOfQueryString = fromOfQueryString + ' INNER JOIN public.\"object-' + parentOfParentName+ '-'+ parentName + '\" as t'+ str(dictPositionsInQuery[key]['pos'])+ onString

    return fromOfQueryString

def positionInQuery(columns, dictPos):   

    popped = columns.pop(0)           

    if columns:
        aux = positionInQuery(columns, dictPos[popped])
    
    else:
        aux = dictPos[popped]['pos']
        

    return aux


#make the bar graph
def graphBar(database, x_axie, condition):
    
    queryConstructionResult = queryConstruction(database, x_axie, 'undefined', condition)

    
    objectStringCallBack = x_axie[:-(len(x_axie.split('***')[len(x_axie.split('***'))-1])+3)]

    #make the bar plot
    bar2 = bar_plot(    queryConstructionResult['valueColumn'], 
                        'cantidad', 
                        database, 
                        database, 
                        queryConstructionResult['valueColumn'], 
                        queryConstructionResult['selectString'], 
                        queryConstructionResult['fromOfQueryString'], 
                        queryConstructionResult['groupByString'], 
                        queryConstructionResult['whereString'],
                        objectStringCallBack,
                        condition,
                        x_axie )
    
    #method that return the script and div that is needed to create the graph in the page  
    script, div = components(bar2)


    return render_template(
        'home/graph.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')

#generate the bar plot
def bar_plot(x_axis_name, y_axis_name, data_db_name, table, column_x, selectString, fromString, groupByString, whereString, objectStringCallBack, conditionCallBack, columnXCallBack):

    #get the data of the database
    #data = Visualization.get_data(data_db_name, table, column_x, condition, innerColumnsCondition)    
    
    data = Visualization.get_data_with_parameters(data_db_name, selectString, fromString, groupByString, whereString)

    database = Visualization.get_database_id(data_db_name)
    databaseId = database['id']

    #get the counts of the data
    y_array = [int(row['count']) for row in data]
    
    #get the x axi value
    x_array = [str(row[column_x]) for row in data]

    
    #create a dictionary that  with the 'x_array' and 'y_array' arrays
    dictionary=dict(  x=x_array, y=y_array)
    
    #transform the dictionary to a 'ColumnDataSource' (needed by the graph)
    source = ColumnDataSource(data=dictionary)

    #generate the graph
    bar = figure(x_range= dictionary['x'], x_axis_label=x_axis_name, y_axis_label=y_axis_name, plot_height=675, plot_width=900, tools="tap, pan, wheel_zoom, save")
    bar.vbar(x='x', top='y', source=source, color='blue', width=0.5)
    bar.y_range.start=0
    
    #on hover tool
    hover_tool = HoverTool(tooltips=[
                (x_axis_name, "@x"),
                (y_axis_name, "@y")
            ])

    if conditionCallBack:

        url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+conditionCallBack+'~~~'+columnXCallBack+' =\'@x\''

    else:

        url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+columnXCallBack+' =\'@x\''
            

    taptool = bar.select(type=TapTool)
    taptool.callback = OpenURL(url=url)
    
    #add on hover tool to the graph
    bar.tools.append(hover_tool)


    #return the graph
    return bar

#return the graph line
def graphLine(database, x_axie, acumulativeX,condition):

    queryConstructionResult = queryConstruction(database, x_axie, 'undefined', condition)

    objectStringCallBack = x_axie[:-(len(x_axie.split('***')[len(x_axie.split('***'))-1])+3)]

    #make the line plot
    line = line_plot(   queryConstructionResult['valueColumn'], 
                        'cantidad', 
                        database, 
                        database, 
                        queryConstructionResult['valueColumn'], 
                        queryConstructionResult['selectString'], 
                        queryConstructionResult['fromOfQueryString'], 
                        queryConstructionResult['groupByString'], 
                        queryConstructionResult['whereString'],
                        objectStringCallBack,
                        condition,
                        x_axie,
                        acumulativeX )
    
    #method that return the script and div that is needed to create the graph in the page 
    script, div = components(line)


    return render_template(
        'home/graph.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')

#line plot with datetimes
def line_plot(x_axis_name, y_axis_name, data_db_name, table, column_x, selectString, fromString, groupByString, whereString, objectStringCallBack, conditionCallBack, columnXCallBack, acumulativeX):
    
    #get the data of the database
    #data = Visualization.get_data(data_db_name, table, column_x, condition, innerColumnsCondition)
    data = Visualization.get_data_with_parameters(data_db_name, selectString, fromString, groupByString, whereString)

    database = Visualization.get_database_id(data_db_name)
    databaseId = database['id']

    #get the counts of the data
    y_array = [int(row['count']) for row in data]
    
    #get the x axi value
    #x_array = [datetime.strptime(str(row[column_x]), '%Y-%m-%d') for row in data]
    x_array_values = [str(row[column_x]) for row in data]
    x_array = [datetime.strptime(str(row[column_x]), '%Y-%m-%d') for row in data]



    #var used to calculate the acumulative count
    countsTotal = []
    count = 0

    #calculate the acumulative count
    for i in range(len(y_array)):
        count = count + y_array[i]
        countsTotal.append(count)

    
    if acumulativeX == '1':

        #create a dictionary that  with the 'x_array' and 'y_array' arrays
        dictionary=dict(  x=x_array, y=countsTotal, x_values=x_array_values)

    else:
        
        #create a dictionary that  with the 'x_array' and 'y_array' arrays
        dictionary=dict(  x=x_array, y=y_array, x_values=x_array_values)     


    #transform the dictionary to a 'ColumnDataSource' (needed by the graph)
    source = ColumnDataSource(data=dictionary)

    #generate the graph
    p = figure( x_axis_type="datetime", x_axis_label=x_axis_name, y_axis_label=y_axis_name, plot_height=675, plot_width=900, tools="tap, pan, wheel_zoom, save")
    p.line(x='x', y='y', source=source, line_width=2)
    p.circle(x='x', y='y', source=source, fill_color="white", size=8)

    #on hover tool
    hover_tool = HoverTool(tooltips=[
            ("Fecha", "@x{%F}"),
            ("Total", "@y")
        ],
        formatters = {'@x': 'datetime'}
            
    )

    #add on hover tool to the graph
    p.tools.append(hover_tool)   

    if conditionCallBack:

        url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+conditionCallBack+'~~~'+columnXCallBack+' =\'@x_values\''

    else:

        url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+columnXCallBack+' =\'@x_values\''
            

    taptool = p.select(type=TapTool)
    taptool.callback = OpenURL(url=url) 

    #return the graph
    return p


#generate the string of the counts for the data table
def counts_query_for_data_table(database, column, condition, pos, parent):

    #get the values of column in the database
    columnData = Visualization.getColumnData(database, 'object-'+parent+'-'+column , condition, pos)

    stringCounts = ''

    #generate the counts
    for x in columnData:

        if str(x[1]) != 'None':

            stringCounts = stringCounts + 'count(case t'+str(pos)+'.\"'+column+'\" when \''+str(x[1])+'\' then 1 else null end) as \"'+ str(x[1]) + '\", '

    #delete the last ', ' of the string
    stringCounts = stringCounts[:-2] 
    
    #add the name of column of the count (used in the headers of the data table)
    columnNames = [str(row[1]) for row in columnData]

    if 'None' in columnNames:

        columnNames.remove('None')

    return [stringCounts, columnNames]
        
    
#generate the data table
def data_table(database, rowName, column, condition):

    queryConstructionResult = queryConstruction(database, rowName, column, condition)

    #Add the count if there is no column defined
    counts = ['COUNT(t0.id) as count', ['cantidad']]

    if column != 'undefined':

        conditionsOfColumn = ''

        #check if there is any condition
        if condition != None:

            #loop through the conditions. The conditions in the string are divided by '***'
            for cond in condition.split(sep='~~~'):

                #check if the columns of the condition is the same of the column of the datatable 
                if (cond[:+len(column)] == column):

                    #add the condition to the string
                    conditionsOfColumn = conditionsOfColumn + cond + '~~~'

            #delete the last '***'
            conditionsOfColumn = conditionsOfColumn[:-3]     

        #counts of the rows in the query
        counts = ''

        queryConditionsOfColumns = ''

        #check if there are conditions of the column selected for the table
        if conditionsOfColumn:

            #call the method to transform the conditions
            queryConditionsOfColumns = conditionsToString(database, conditionsOfColumn, queryConstructionResult['dictPositionsInQuery']) 

        columnsToAddToDict = column.split(sep='***')
        columnsToAddToDict.append('object')

        valueColumnCond = columnsToAddToDict[len(columnsToAddToDict)-2] 
        valueColumnObjectParent = columnsToAddToDict[len(columnsToAddToDict)-3] 
        posCond = positionInQuery(columnsToAddToDict, queryConstructionResult['dictPositionsInQuery'])
            
            

        #generate the counts for the columns needed
        counts = counts_query_for_data_table(database, valueColumnCond , queryConditionsOfColumns, posCond, valueColumnObjectParent)       

    #data = Visualization.get_data_for_data_table(database, valueColumn, column, conditionAndColumns[0], conditionAndColumns[1], counts[0])    

    data = Visualization.get_data_with_parameters(database, queryConstructionResult['groupByString'] + ', ' + counts[0], queryConstructionResult['fromOfQueryString'], queryConstructionResult['groupByString'], queryConstructionResult['whereString'])
    
    #Array of 'rowNames' returned by the query
    columnRow = [str(row[ queryConstructionResult['valueColumn']]) for row in data]

    #create a dictionary that  will be used by the data table
    dictionary = dict()

    #add the array to the dictionary
    dictionary[rowName] = columnRow

    #add the counts to the table and the headers of the columns of counts in the table
    for x in range(len(counts[1])):
        dictionary[counts[1][x]] = [int(row[x+1]) for row in data]    

    #transform the dictionary to a 'ColumnDataSource' (needed by the table)
    source = ColumnDataSource(dictionary)

    #add the first column
    dataTableColumns = [TableColumn(field=rowName, title=queryConstructionResult['valueColumn'])]

    #add the others columns
    for x in counts[1]:
        dataTableColumns.append(TableColumn(field=x, title=x))

    #create the data table
    dataTable = DataTable(source=source, columns=dataTableColumns, index_position=None, width=900, height=640)

    #method that return the script and div that is needed to create the graph in the page 
    script, div = components(dataTable)

    #return the template
    return render_template(
        'home/graph.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')


#generate the pie chart
def pie_plot(rowName, data_db_name, table, column_x, selectString, fromString, groupByString, whereString, objectStringCallBack, conditionCallBack, columnXCallBack):

    #get the data of the database
    #data = Visualization.get_data(data_db_name, table, column_x, condition, innerColumnsCondition)
    data = Visualization.get_data_with_parameters(data_db_name, selectString, fromString, groupByString, whereString)

    database = Visualization.get_database_id(data_db_name)
    databaseId = database['id']

    #get the names of each portion of the graph
    rowData = [str(row[rowName]) for row in data]

    #get the counts of the data
    counts = [int(row['count']) for row in data]


    inspectString = [ (columnXCallBack+' =\''+str(row[rowName])+'\'') for row in data]

    if len(data)>10:

        countsToOthers= counts[9:len(data)]
        
        counts = counts [0:9]
        rowData = rowData [0:9]
        inspectString = inspectString[0:9]

        inspectStringsToGenerateStrings = [ columnXCallBack+' !=\''+str(row[rowName])+'\'' for row in data]
        inspectStringsToGenerateStrings = inspectStringsToGenerateStrings[0:9]

        inspectStringToOthers = '~~~'.join(inspectStringsToGenerateStrings)
        
        totalOthers = sum(countsToOthers)

        counts.append(totalOthers)
        rowData.append('otros')
        inspectString.append(inspectStringToOthers)

    #create the dictionary
    dictionary = {}

    #put the data in a dictionary
    for i in range(len(rowData)):
        dictionary[rowData[i]] = counts[i]

    #generate the data structure needed by the graph
    data = pd.Series(dictionary).reset_index(name='value').rename(columns={'index':rowName})
    
    #calculate the total of the counts
    totalSum = data['value'].sum()

    data['inspectString'] = inspectString

    #calculate the angle of each portion of the pie chart
    data['angle'] = data['value']/totalSum * 2*pi
    data['percentage'] = data['value']/totalSum * 100
    
    #calculate the color for each portion
    if len(data['angle'])<=2:
        colors = Category10[3]
        data['color'] = colors[:-(3-len(data['angle']))]
    else:    
        data['color'] = Category10[(len(data['angle']))]

        
    #generate the graph
    p = figure(plot_height=675, plot_width=900, x_range=(-0.5, 1.0), tools="tap, pan, wheel_zoom, save")
    p.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white", fill_color='color', legend_field=rowName, source=data)

    #on hover tool 
    hover_tool = HoverTool(tooltips=[
                (rowName, "@"+rowName),
                ("porcentaje", "@percentage"+" %"),
                ("cantidad", "@value")
            ])

    #add on hover tool to the graph
    p.tools.append(hover_tool)  

    if conditionCallBack:

        url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+conditionCallBack+'~~~@inspectString'

    else:

        url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&@inspectString'
    
    
    taptool = p.select(type=TapTool)
    taptool.callback = OpenURL(url=url)         


    #return the graph
    return p

#generate the pie chart
def pie_chart(database, rowName, condition):

    queryConstructionResult = queryConstruction(database, rowName, 'undefined', condition)

    objectStringCallBack = rowName[:-(len(rowName.split('***')[len(rowName.split('***'))-1])+3)]


    #call the method that generate the graph
    graph = pie_plot(   queryConstructionResult['valueColumn'], 
                        database, 
                        database, 
                        queryConstructionResult['valueColumn'], 
                        queryConstructionResult['selectString'], 
                        queryConstructionResult['fromOfQueryString'], 
                        queryConstructionResult['groupByString'], 
                        queryConstructionResult['whereString'],
                        objectStringCallBack,
                        condition,
                        rowName)
    

    #method that return the script and div that is needed to create the graph in the page 
    script, div = components(graph)
 
    return render_template(
        'home/graph.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')


#
def dot_chart(database, rowName, column, condition):

    queryConstructionResult = queryConstruction(database, rowName, column, condition)

    objectRowStringCallBack = rowName[:-(len(rowName.split('***')[len(rowName.split('***'))-1])+3)]

    valueColumn = 'undefined'

    columnToGroupBy = ''

    y_axis_name = 'cantidad'

    if column != 'undefined':

        columnsToAddToDict = column.split(sep='***')
        columnsToAddToDict.append('object')

        valueColumn = columnsToAddToDict[len(columnsToAddToDict)-2] 
        posColumn = positionInQuery(columnsToAddToDict, queryConstructionResult['dictPositionsInQuery'])
        columnToGroupBy = ', t'+str(posColumn)+'.\"'+valueColumn+'\"'

        y_axis_name = valueColumn


    graph = dot_plot(    queryConstructionResult['valueColumn'], 
                        y_axis_name, 
                        database, 
                        database, 
                        queryConstructionResult['valueColumn'], 
                        queryConstructionResult['selectString'] + columnToGroupBy, 
                        queryConstructionResult['fromOfQueryString'], 
                        queryConstructionResult['groupByString'] + columnToGroupBy, 
                        queryConstructionResult['whereString'],
                        valueColumn,
                        objectRowStringCallBack,
                        condition,
                        rowName,
                        column )
    

    #method that return the script and div that is needed to create the graph in the page 
    script, div = components(graph)
 
    return render_template(
        'home/graph.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')


def dot_plot(x_axis_name, y_axis_name, data_db_name, table, column_x, selectString, fromString, groupByString, whereString, column_y, objectStringCallBack, conditionCallBack, columnXCallBack, columnYCallBack):

    data = Visualization.get_data_with_parameters(data_db_name, selectString, fromString, groupByString, whereString)

    database = Visualization.get_database_id(data_db_name)
    databaseId = database['id']


    #get the counts of the data
    counts = [int(row['count']) for row in data]
    maxCount = max(counts)
    radio = []
    size = []

    #put the radio of the circle depending of the count
    for count in counts:

        #radio.append((0.14/maxCount)*count + 0.06)
        size.append((30/maxCount)*count + 10)


    
    #get the x axi value
    x_array = [str(row[column_x]) for row in data]

    xCategorical = list(set(x_array))

    if column_y == 'undefined':

        #create a dictionary that  with the 'x_array' and 'y_array' arrays
        dictionary=dict(  x=x_array, y=counts,  size=size)
        
        #transform the dictionary to a 'ColumnDataSource' (needed by the graph)
        source = ColumnDataSource(data=dictionary)
     
        #p = figure(y_range=yCategorical, x_range=xCategorical, title="Title", plot_height=575, plot_width=900)
        
        p = figure(x_range=xCategorical,  plot_height=675, plot_width=900, tools="tap, pan, wheel_zoom, save")
        p.y_range.start=-1
        p.y_range.end= maxCount+3

        #p.circle(x='x', y='y', source=source, fill_color="blue", radius='radio')
        p.circle(x='x', y='y', source=source, fill_color="blue", size='size')


        #on hover tool
        hover_tool = HoverTool(tooltips=[
                    (x_axis_name, "@x"),
                    (y_axis_name, "@y")
                ])

        if conditionCallBack:

            url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+conditionCallBack+'~~~'+columnXCallBack+' =\'@x\''

        else:

            url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+columnXCallBack+' =\'@x\''
        
        
    else:

        y_array = [(row[column_y]) for row in data]

        y_array = list(set(y_array))

        y_array.sort()

        y_array = [str(x) for x in y_array]

        yCategorical = y_array

        y_array = [str(row[column_y]) for row in data]

        #create a dictionary that  with the 'x_array' and 'y_array' arrays
        dictionary=dict(  x=x_array, y=y_array, counts=counts, size=size)
        
        #transform the dictionary to a 'ColumnDataSource' (needed by the graph)
        source = ColumnDataSource(data=dictionary)
     
        #p = figure(y_range=yCategorical, x_range=xCategorical, title="Title", plot_height=575, plot_width=900)
        
        p = figure(x_range=xCategorical, y_range=yCategorical,  plot_height=675, plot_width=900, tools="tap, pan, wheel_zoom, save")

        #p.circle(x='x', y='y', source=source, fill_color="blue", radius='radio')
        p.circle(x='x', y='y', source=source, fill_color="blue", size='size')


        #on hover tool
        hover_tool = HoverTool(tooltips=[
                    (x_axis_name, "@x"),
                    (y_axis_name, "@y"),
                    ('cantidad', "@counts")
                ])

        if conditionCallBack:

            url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+conditionCallBack+'~~~'+columnXCallBack+' =\'@x\''+'~~~'+columnYCallBack+' =\'@y\''

        else:

            url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+columnXCallBack+' =\'@x\''+'~~~'+columnYCallBack+' =\'@y\''
        

    p.tools.append(hover_tool) 

    taptool = p.select(type=TapTool)
    taptool.callback = OpenURL(url=url)  
 

    return p

def scatter_chart(database, rowName, column, dispersionX, dispersionY, condition):

    queryConstructionResult = queryConstruction(database, rowName, column, condition)

    objectRowStringCallBack = rowName[:-(len(rowName.split('***')[len(rowName.split('***'))-1])+3)]


    valueColumn = 'undefined'

    columnToGroupBy = ''

    if column != 'undefined':

        columnsToAddToDict = column.split(sep='***')
        columnsToAddToDict.append('object')

        valueColumn = columnsToAddToDict[len(columnsToAddToDict)-2] 
        posColumn = positionInQuery(columnsToAddToDict, queryConstructionResult['dictPositionsInQuery'])
        columnToGroupBy = ', t'+str(posColumn)+'.\"'+valueColumn+'\"'


    graph = scatter_plot(    queryConstructionResult['valueColumn'], 
                        'cantidad', 
                        database, 
                        queryConstructionResult['valueColumn'], 
                        queryConstructionResult['selectString'] + columnToGroupBy, 
                        queryConstructionResult['fromOfQueryString'], 
                        queryConstructionResult['groupByString'] + columnToGroupBy, 
                        queryConstructionResult['whereString'],
                        valueColumn,
                        dispersionX,
                        dispersionY,
                        objectRowStringCallBack,
                        condition,
                        rowName,
                        column )
    

    #method that return the script and div that is needed to create the graph in the page 
    script, div = components(graph)
 
    return render_template(
        'home/graph.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')

def scatter_plot(x_axis_name, y_axis_name, data_db_name, column_x, selectString, fromString, groupByString, whereString, column_y, dispersionX, dispersionY, objectStringCallBack, conditionCallBack, columnXCallBack, columnYCallBack):

    data = Visualization.get_data_with_parameters_for_scatter(data_db_name, groupByString, fromString, groupByString, whereString)

    database = Visualization.get_database_id(data_db_name)
    databaseId = database['id']
    
    x_array = [(row[column_x]) for row in data]

    x_array = list(set(x_array))

    x_array.sort()

    x_array = [str(x) for x in x_array]

    xCategorical = x_array

    #get the x axi value
    x_array = [str(row[column_x]) for row in data]

    if column_y == 'undefined':

        y_array = [ 'unico valor' for row in data]

        #create a dictionary that  with the 'x_array' and 'y_array' arrays
        dictionary=dict(  x=x_array, y=y_array)
        
        #transform the dictionary to a 'ColumnDataSource' (needed by the graph)
        source = ColumnDataSource(data=dictionary)
     
        #p = figure(y_range=yCategorical, x_range=xCategorical, title="Title", plot_height=575, plot_width=900)
        
        p = figure(x_range=xCategorical, y_range=['unico valor'], plot_height=675, plot_width=900, tools="tap, pan, wheel_zoom, save")

        p.circle(x=jitter('x',width=float(dispersionX), range = p.x_range), y=jitter('y',width=float(dispersionY), range = p.y_range), source=source, fill_color="blue", size=30, alpha= 0.3)

        #on hover tool
        hover_tool = HoverTool(tooltips=[
                    (x_axis_name, "@x")
                ])

        if conditionCallBack:

            url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+conditionCallBack+'~~~'+columnXCallBack+' =\'@x\''

        else:

            url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+columnXCallBack+' =\'@x\''

    else:

        y_array = [(row[column_y]) for row in data]

        y_array = list(set(y_array))

        y_array.sort()

        y_array = [str(x) for x in y_array]

        yCategorical = y_array

        y_array = [str(row[column_y]) for row in data]

        #create a dictionary that  with the 'x_array' and 'y_array' arrays
        dictionary=dict(  x=x_array, y=y_array)
        
        #transform the dictionary to a 'ColumnDataSource' (needed by the graph)
        source = ColumnDataSource(data=dictionary)
        
        p = figure(x_range=xCategorical, y_range=yCategorical, plot_height=675, plot_width=900, tools="tap, pan, wheel_zoom, save")

        p.circle(x=jitter('x',width=float(dispersionX), range = p.x_range), y=jitter('y',width=float(dispersionY), range = p.y_range), source=source, fill_color="blue", size=30, alpha= 0.3)

        #on hover tool
        hover_tool = HoverTool(tooltips=[
                    (x_axis_name, "@x"),
                    (y_axis_name, "@y")
                ])

        if conditionCallBack:

            url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+conditionCallBack+'~~~'+columnXCallBack+' =\'@x\''+'~~~'+columnYCallBack+' =\'@y\''

        else:

            url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+columnXCallBack+' =\'@x\''+'~~~'+columnYCallBack+' =\'@y\''

    p.tools.append(hover_tool)  

    taptool = p.select(type=TapTool)
    taptool.callback = OpenURL(url=url) 

    return p

def map_chart(database, latitude, longitude, condition):

    queryConstructionResult = queryConstruction(database, latitude, longitude, condition)

    objectRowStringCallBack = latitude[:-(len(latitude.split('***')[len(latitude.split('***'))-1])+3)]

    valueColumn = 'undefined'

    columnToGroupBy = ''

    y_axis_name = 'cantidad'

    if longitude != 'undefined':

        columnsToAddToDict = longitude.split(sep='***')
        columnsToAddToDict.append('object')

        valueColumn = columnsToAddToDict[len(columnsToAddToDict)-2] 
        posColumn = positionInQuery(columnsToAddToDict, queryConstructionResult['dictPositionsInQuery'])
        columnToGroupBy = ', t'+str(posColumn)+'.\"'+valueColumn+'\"'

        y_axis_name = valueColumn


    graph = map_plot(    queryConstructionResult['valueColumn'], 
                        y_axis_name, 
                        database, 
                        database, 
                        queryConstructionResult['valueColumn'], 
                        queryConstructionResult['selectString'] + columnToGroupBy, 
                        queryConstructionResult['fromOfQueryString'], 
                        queryConstructionResult['groupByString'] + columnToGroupBy, 
                        queryConstructionResult['whereString'],
                        valueColumn,
                        objectRowStringCallBack,
                        condition,
                        latitude,
                        longitude )
    

    #method that return the script and div that is needed to create the graph in the page 
    script, div = components(graph)
 
    return render_template(
        'home/graph.html',
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')




def map_plot(x_axis_name, y_axis_name, data_db_name, table, column_x, selectString, fromString, groupByString, whereString, column_y, objectStringCallBack, conditionCallBack, columnXCallBack, columnYCallBack):

    data = Visualization.get_data_with_parameters(data_db_name, 't0.id, '+selectString, fromString, 't0.id, '+groupByString, whereString)

    database = Visualization.get_database_id(data_db_name)
    databaseId = database['id']
    
    k = 6378137

    #get the x axi value
    latitude_array = [np.log(np.tan((90 + float(str(row[column_x]))) * np.pi/360.0)) * k for row in data]
    longitude_array = [float(str(row[column_y]))*(k * pi/180.0) for row in data]
    ids = [(row['id']) for row in data]

    #latitude_array = []
    #longitude_array = []


    #create a dictionary that  with the 'x_array' and 'y_array' arrays
    dictionary=dict(  lat=latitude_array, lon=longitude_array, id=ids)
    
    #transform the dictionary to a 'ColumnDataSource' (needed by the graph)
    source = ColumnDataSource(data=dictionary)


    tile_provider = get_provider(CARTODBPOSITRON)

    k = 6378137
    #df["x"] = df[lon] * (k * np.pi/180.0)
    #df["y"] = np.log(np.tan((90 + df[lat]) * np.pi/360.0)) * k

    # range bounds supplied in web mercator coordinates
    p = figure(x_range=(-20000000, 20000000), y_range=(-6500000, 9000000), plot_height=675, plot_width=900,
               x_axis_type="mercator", y_axis_type="mercator", tools="tap, pan, wheel_zoom, save")
    p.add_tile(tile_provider)

    #source = ColumnDataSource(
    #data=dict(lat=[ np.log(np.tan((90 + 30.29) * np.pi/360.0)) * k, np.log(np.tan((90 + 30.20) * np.pi/360.0)) * k  , np.log(np.tan((90 + 30.29) * np.pi/360.0)) * k ],
    #          lon=[-97.70*(k * pi/180.0), -97.74*(k * pi/180.0), -97.78*(k * pi/180.0)])
    #)

    p.circle(x="lon", y="lat", size=10, fill_color="blue", fill_alpha=0.4, source=source)


    url = (url_for('home'))+'inspectRows/'+str(databaseId)+'&'+objectStringCallBack+'&'+data_db_name+' =\'@id\''

    taptool = p.select(type=TapTool)
    taptool.callback = OpenURL(url=url) 

    return p



#return the values of a table
def ajaxGetColumnData(database, column):

    dictPositionsInQuery = {}

    columnsToAddToDict = column.split(sep='***')
    columnsToAddToDict.append('object')

    aux = addPosInQuery(columnsToAddToDict, dictPositionsInQuery, 0)

    dictPositionsInQuery = aux[0]

    fromOfQueryString = 'public.\"'+ database + '\" as t0 '

    fromOfQueryString = generateSelect(dictPositionsInQuery[database], fromOfQueryString , database, database)  

    columnsToAddToDict = column.split(sep='***')
    columnsToAddToDict.append('object')

    valueColumn = columnsToAddToDict[len(columnsToAddToDict)-2] 
    pos = positionInQuery(columnsToAddToDict, dictPositionsInQuery)

    groupByString = 't'+str(pos)+'.\"'+valueColumn+'\"'

    selectString = groupByString + ',  COUNT(t'+str(pos)+'.id) as count'


    ajaxData = Visualization.get_data_with_parameters(database, selectString, fromOfQueryString, groupByString,'')
    
    #ajaxData = Visualization.getColumnData(database, column, '')

    

    y = 0
    if(str(type(ajaxData[0][0])) == "<class 'datetime.date'>"):
        for x in ajaxData:
            x[0] = str(x[0])


    return jsonify(result = ajaxData)


def recursion_query(databaseStructure, dictPositionsInQuery, pos, objectString, select, positionOfTheQuery, posOfQueryReturn):

    dictPositionsInQueryRecursion = dictPositionsInQuery
    posRecursion = pos
    selectToReturn = select
    positionOfTheQueryRecusion = positionOfTheQuery
    posOfQueryReturnRecursion = posOfQueryReturn

    for x in databaseStructure.keys():

        stringToAdd = objectString+'***'+x

        columnsToAddToDict = stringToAdd.split(sep='***')
        if not isinstance(databaseStructure[x], dict):            
            columnsToAddToDict.append('object')

        aux = addPosInQuery(columnsToAddToDict, dictPositionsInQueryRecursion, posRecursion)
        dictPositionsInQueryRecursion = aux[0]
        posRecursion = aux[1]


        
        if isinstance(databaseStructure[x], dict):

            selectToReturn = selectToReturn + 't'+str(positionInQuery((objectString+'***'+x).split(sep='***'), dictPositionsInQuery))+'.id_'+((objectString+'***'+x).split(sep='***')[len((objectString+'***'+x).split(sep='***'))-1])+', ' 

            positionOfTheQueryRecusion[str(posOfQueryReturnRecursion)] = objectString+'***'+x+'***id_'+x
            posOfQueryReturnRecursion = posOfQueryReturnRecursion + 1     

            aux = recursion_query(databaseStructure[x], dictPositionsInQueryRecursion, posRecursion, objectString+'***'+x, selectToReturn, positionOfTheQueryRecusion, posOfQueryReturnRecursion)
            dictPositionsInQueryRecursion= aux[0]
            posRecursion = aux[1]
            selectToReturn = aux[2]
            positionOfTheQueryRecusion = aux[3]
            posOfQueryReturnRecursion = aux[4]

        else:
    
            selectToReturn = selectToReturn + ' t'+ str(posRecursion-1) +'.'+x+','

            positionOfTheQueryRecusion [str(posOfQueryReturnRecursion)] = stringToAdd
            posOfQueryReturnRecursion = posOfQueryReturnRecursion + 1

    return [dictPositionsInQueryRecursion, posRecursion, selectToReturn, positionOfTheQueryRecusion, posOfQueryReturnRecursion]        

def inspect_rows(databaseId, objectString, condition):

    #get the columns of the database
    columns = Visualization.get_db_data(databaseId)
    
    #get the database
    database = Visualization.get_database(databaseId)

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

    objectColumns = objectString.split(sep='***')

    objectStringLast = objectColumns[len(objectColumns)-1]
    
    objectColumns.pop(0)

    for column in objectColumns:
        databaseStructure = databaseStructure[column]

    dictPositionsInQuery = {}
    pos = 0

    select = ''


    posOfQueryReturn = 1
    positionOfTheQuery = {}

    positionOfTheQuery['0'] = objectString+'***id'

    for x in databaseStructure.keys():

        stringToAdd = objectString+'***'+x

        columnsToAddToDict = stringToAdd.split(sep='***')
        if not isinstance(databaseStructure[x], dict):            
            columnsToAddToDict.append('object')

        aux = addPosInQuery(columnsToAddToDict, dictPositionsInQuery, pos)
        dictPositionsInQuery = aux[0]
        pos = aux[1]
        
        if isinstance(databaseStructure[x], dict):         

            select = select + 't'+str(positionInQuery((objectString+'***'+x).split(sep='***'), dictPositionsInQuery))+'.id_'+((objectString+'***'+x).split(sep='***')[len((objectString+'***'+x).split(sep='***'))-1])+', ' 

            positionOfTheQuery[str(posOfQueryReturn)] = objectString+'***'+x+'***id_'+x
            posOfQueryReturn = posOfQueryReturn + 1        

            aux = recursion_query(databaseStructure[x], dictPositionsInQuery, pos, objectString+'***'+x, select, positionOfTheQuery, posOfQueryReturn)
            dictPositionsInQuery= aux[0]
            pos = aux[1]
            select = aux[2]
            positionOfTheQuery = aux[3] 
            posOfQueryReturn = aux[4]

        else:

            select = select + ' t'+ str(pos-1) +'.\"'+x+'\",'
            
            positionOfTheQuery[str(posOfQueryReturn)] = stringToAdd
            posOfQueryReturn = posOfQueryReturn + 1        

    conditionQueryString = ''

    if condition != None:
        for cond in condition.split(sep='~~~'):
            
            #get the name of the column (first part of the condition)
            columnCondition = cond.split(sep='=')[0]
            
            columnCondition = columnCondition[:-1].strip()

            columnsToAddToDict = columnCondition.split(sep='***')
            
            if columnCondition != database['name']:
                
                columnsToAddToDict.append('object')
            
            aux = addPosInQuery(columnsToAddToDict, dictPositionsInQuery, pos)   

            dictPositionsInQuery = aux[0]
            pos = aux[1]
        
        #call the method to transform the conditions
        conditionQueryString = conditionsToString(database['name'], condition, dictPositionsInQuery)

    fromOfQueryString = 'public.\"'+  database['name'] + '\" as t0 '

    fromOfQueryString = generateSelect(dictPositionsInQuery[database['name']], fromOfQueryString , database['name'], database['name'])  

    if database['name'] == objectString:

        selectString = 't'+str(positionInQuery(objectString.split(sep='***'), dictPositionsInQuery))+'.id'+', ' + select[:-1]

    else:

        selectString = 't'+str(positionInQuery(objectString.split(sep='***'), dictPositionsInQuery))+'.id_'+objectString.split(sep='***')[len(objectString.split(sep='***'))-1]+', ' + select[:-1]

    fromOfQueryString = fromOfQueryString.replace("INNER JOIN","LEFT OUTER JOIN")

    dataQuery = Visualization.get_data_with_parameters_for_inspection(database['name'], selectString, fromOfQueryString, conditionQueryString)

    data = {}
    dataIds= []

    for row in dataQuery:

        rowPosition = 1

        if row[0] not in dataIds:

            dataIds.append(row[0])
            data[str(row[0])] = {} 
            
            for x in databaseStructure.keys():
                
                if isinstance(databaseStructure[x], dict):

                    aux = recursionDataToReturn(rowPosition, row, databaseStructure[x], data[str(row[0])], x)

                    rowPosition = aux[0]

                else:
                    data[str(row[0])][x] = row[rowPosition]

                    rowPosition = rowPosition + 1         

        else:

            for x in databaseStructure.keys():
                
                if isinstance(databaseStructure[x], dict):

                    aux = recursionDataToReturn(rowPosition, row, databaseStructure[x], data[str(row[0])], x)

                    rowPosition = aux[0]

                else:

                    rowPosition = rowPosition + 1                                 
                     
    
    return render_template('home/inspectRows.html', data=data, database=database['name'], objectString=objectStringLast) 


def recursionDataToReturn(rowPosition, row, databaseStructure, data, column):   

    if column not in data:

        data[column] = []

    allKeys = []

    if data[column] :
        allKeys = set().union(*(d.keys() for d in data[column]))

    columnToAdd = {}

    rowPositionId = rowPosition

    rowPosition = rowPosition + 1

    if str(row[rowPositionId]) not in allKeys:

        columnToAdd[str(row[rowPositionId])] = {}

        for x in databaseStructure.keys():
                
                if isinstance(databaseStructure[x], dict):
                    
                    aux = recursionDataToReturn(rowPosition, row, databaseStructure[x], columnToAdd[str(row[rowPositionId])], x)

                    rowPosition = aux[0]

                else:
                    columnToAdd[str(row[rowPositionId])][x] = row[rowPosition]

                    rowPosition = rowPosition + 1 
    
    else:

        for x in databaseStructure.keys():
                
            if isinstance(databaseStructure[x], dict):
             
                aux = recursionDataToReturn(rowPosition, row, databaseStructure[x], columnToAdd[str(row[rowPositionId])], x)

                rowPosition = aux[0]

            else:

                rowPosition = rowPosition + 1         

    data[column].append(columnToAdd)                

    return [rowPosition]            
