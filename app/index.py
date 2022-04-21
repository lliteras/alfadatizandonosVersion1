from os import path
from flask import Flask
import psycopg2
import psycopg2.extras
from db import get_db
from flask_session import Session
import json

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#@app.route("/")
#def hello():
#    cursor = get_db().cursor(cursor_factory = psycopg2.extras.DictCursor)
#    query = "SELECT *  FROM public.user"
#    cursor.execute(query)
#    list_users = cursor.fetchall()
#    return json.dumps(list_users)

from resources import user, visualization, home, socialGraph, worldcloud
from resources.activities import activities
from resources.datasets import datasets
from resources.configuration import configuration
from resources.profile import profile
from resources.courses import course
from resources.educational_establishments import extracting_data

app.add_url_rule('/', 'home', home.home)

app.add_url_rule('/graphLine/<database>&<x_axie>&<acumulativeX>', 'graph_line', visualization.graphLine, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/graphLine/<database>&<x_axie>&<acumulativeX>&<condition>', 'graph_line', visualization.graphLine, methods=['GET'])

app.add_url_rule('/graphBar/<database>&<x_axie>', 'graph_bar', visualization.graphBar, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/graphBar/<database>&<x_axie>&<condition>', 'graph_bar', visualization.graphBar, methods=['GET'])

app.add_url_rule('/dataTable/<database>&<rowName>&<column>', 'data_table', visualization.data_table, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/dataTable/<database>&<rowName>&<column>&<condition>', 'data_table', visualization.data_table, methods=['GET'])

app.add_url_rule('/pieChart/<database>&<rowName>', 'pie_chart', visualization.pie_chart, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/pieChart/<database>&<rowName>&<condition>', 'pie_chart', visualization.pie_chart, methods=['GET'])


app.add_url_rule('/dotChart/<database>&<rowName>&<column>', 'dot_chart', visualization.dot_chart, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/dotChart/<database>&<rowName>&<column>&<condition>', 'dot_chart', visualization.dot_chart, methods=['GET'])

app.add_url_rule('/scatterChart/<database>&<rowName>&<column>&<dispersionX>&<dispersionY>', 'scatter_chart', visualization.scatter_chart, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/scatterChart/<database>&<rowName>&<column>&<dispersionX>&<dispersionY>&<condition>', 'scatter_chart', visualization.scatter_chart, methods=['GET'])


app.add_url_rule('/mapChart/<database>&<latitude>&<longitude>', 'map_char', visualization.map_chart, methods=['GET'], defaults={'condition':None})

app.add_url_rule('/mapChart/', 'map_plot', visualization.map_plot, methods=['GET'])

app.add_url_rule('/loginForm', 'loginForm', user.login_form, methods=['GET'])
app.add_url_rule('/login', 'login', user.login, methods=['POST'])
app.add_url_rule('/logout', 'logout', user.logout, methods=['GET'])


app.add_url_rule('/registerForm', 'registerForm', user.register_form, methods=['GET'])
app.add_url_rule('/showRegister', 'showRegister', user.show_register, methods=['GET'])
app.add_url_rule('/register', 'register', user.register, methods=['POST'])

app.add_url_rule('/forgotPassword', 'forgotPassword', user.forgotPassword, methods=['GET'])

app.add_url_rule('/plotter/<int:Bid>', 'plotter', visualization.plotter, methods=['GET'], defaults={'activityId':None})
app.add_url_rule('/plotter/<int:Bid>&<int:activityId>', 'plotter', visualization.plotter, methods=['GET'])
app.add_url_rule('/plotter/ajax/<database>&<column>', 'ajax_get_column_data', visualization.ajaxGetColumnData, methods=['GET'])

app.add_url_rule('/dragAndDrop', 'dragAndDrop', home.dragAndDrop, methods=['GET'])
app.add_url_rule('/dragAndDrop/uploadFile', 'uploadFile', home.uploadFile, methods=['POST'])
app.add_url_rule('/dragAndDrop/configurateUploadCSV', 'configurateUploadCSV', home.configurateUploadCSV, methods=['POST'])
app.add_url_rule('/dragAndDrop/configurateUploadJSON', 'configurateUploadJSON', home.configurateUploadJSON, methods=['POST'])

app.add_url_rule('/activities', 'activities', activities.activities, methods=['GET'])
app.add_url_rule('/activities/new_activity/<course_id>', 'new_activity', activities.new_activity)
app.add_url_rule('/activities/create_activity', 'create_activity', activities.create_activity, methods=['POST'])
app.add_url_rule('/activities/view_activity/<id>', 'view_activity', activities.view_activity)
app.add_url_rule('/activities/view_activity_data/<id>', 'view_activity_data', activities.view_activity_data)
app.add_url_rule('/resolverActividad/<int:id>', 'resolverActividad', activities.solveActivity)


app.add_url_rule('/addPlotterResolutionToActivity', 'add_plotter_resolution_to_activity', activities.addPlotterResolutionToActivity, methods=['POST'])
app.add_url_rule('/addSocialGraphResolutionToActivity', 'add_social_graph_resolution_to_activity', activities.addSocialGraphResolutionToActivity, methods=['POST'])
app.add_url_rule('/viewResolutionGraph/<int:resolutionId>', 'view_resolution_graph', activities.viewResolutionGraph, methods=['GET'])
app.add_url_rule('/viewResolutionSocialGraph/<int:resolutionId>', 'view_resolution_social_graph', activities.viewResolutionSocialGraph, methods=['GET'])




app.add_url_rule('/activities/correct/<activity_id>&<user_id>', 'correct_activity_view', activities.correct_activity_view)
app.add_url_rule('/activities/viewCorrectedActivity/<activity_id>&<user_id>', 'view_corrected_activity', activities.viewCorrectedActivity)

app.add_url_rule('/activity/correctActivity/<activity_id>&<user_id>', 'correct_activity', activities.correct_activity, methods=['POST'])

app.add_url_rule('/datasets', 'datasets', datasets.datasets, methods=['GET'])

app.add_url_rule('/configuration', 'configuration', configuration.configuration, methods=['GET'])
app.add_url_rule('/configuration_AJAX/<int:page>&<int:filtered>', 'configurationAJAX', configuration.configuration_AJAX)
app.add_url_rule('/update_establishment_file', 'update_establishment_file', configuration.upload_establishment_file, methods=['POST'])
app.add_url_rule('/cambiar_rol/<user_id>/<role_id>', 'cambiar_rol', configuration.cambiar_rol, methods=['GET'])
app.add_url_rule('/addRoleToUser/<role_id>&<user_id>', 'addRole', configuration.add_role)
app.add_url_rule('/deleteRoleToUser/<role_id>&<user_id>', 'deleteRole', configuration.delete_role, methods=['PUT'])
app.add_url_rule('/changeActualRole/<rolename>', 'changeActualRole', user.changeActualRole)


app.add_url_rule('/get_establishments', 'get_establishments', extracting_data.extract_data, methods=['GET'])
app.add_url_rule('/showRegister/<province>', 'get_cities_by_province', extracting_data.get_cities_by_province, methods=['GET'])
app.add_url_rule('/showRegister/ciudad/<city>', 'get_establishment_by_city', extracting_data.get_establishments_by_city, methods=['GET'])

app.add_url_rule('/datasets', 'datasets', datasets.datasets, methods=['GET'])


app.add_url_rule('/courses', 'courses', course.get_courses, methods=['GET'])
app.add_url_rule('/courses/<course_id>', 'course<course_id>', course.view_course, methods=['GET'])
#Usuario existe
app.add_url_rule('/courses/userExist/<username>', 'userExist', user.user_exist)
app.add_url_rule('/courses/inviteUserToCourse/<username>&<course_id>', 'inviteUser', course.invite_user_to_course)
app.add_url_rule('/courses/isStudentOnCourse/<username>&<course_id>', 'isUserOnCourse', course.is_user_on_course)
app.add_url_rule('/new_course', 'new_courses', course.new_course, methods=['GET'])
app.add_url_rule('/create_course', 'create_course', course.create_course, methods=['POST'])
app.add_url_rule('/courseAddDataset', 'course_add_dataset', course.course_add_dataset, methods=['POST'])


#TWITTER
app.add_url_rule('/twitterSearch/<stringToSearch>&<int:topQuantity>&<int:articles>&<int:prep>&<int:pron>&<int:conj>&<int:adv>&<int:verbos>&<int:links>', 'api_twitter_search', socialGraph.api_twitter_search, methods=['GET'])
app.add_url_rule('/twitter', 'twitter_search', socialGraph.twitter_search, methods=['GET'], defaults={'noNav':0})
app.add_url_rule('/twitter/<int:noNav>', 'twitter_search', socialGraph.twitter_search, methods=['GET'])

#INSPECT
app.add_url_rule('/inspectRows/<databaseId>&<objectString>', 'inspect_rows', visualization.inspect_rows, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/inspectRows/<databaseId>&<objectString>&<condition>', 'inspect_rows', visualization.inspect_rows, methods=['GET'])
app.add_url_rule('/inspectRows/<databaseId>&<objectString>&<condition>', 'inspect_rows', visualization.inspect_rows, methods=['GET'])

#DATASETS
app.add_url_rule('/datasets/indexPublics', 'datasets_index_publics', datasets.indexPublics, methods=['GET'], defaults={'page':1, 'condition':None})
app.add_url_rule('/datasets/indexPublics/<int:page>', 'datasets_index_publics', datasets.indexPublics, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/datasets/indexPublics/<int:page>&<condition>', 'datasets_index_publics', datasets.indexPublics, methods=['GET'])

app.add_url_rule('/datasets/indexProtecteds', 'datasets_index_protecteds', datasets.indexProtecteds, methods=['GET'], defaults={'page':1, 'condition':None})
app.add_url_rule('/datasets/indexProtecteds/<int:page>', 'datasets_index_protecteds', datasets.indexProtecteds, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/datasets/indexProtecteds/<int:page>&<condition>', 'datasets_index_protecteds', datasets.indexProtecteds, methods=['GET'])

app.add_url_rule('/datasets/indexPrivates', 'datasets_index_privates', datasets.indexPrivates, methods=['GET'], defaults={'page':1, 'condition':None})
app.add_url_rule('/datasets/indexPrivates/<int:page>', 'datasets_index_privates', datasets.indexPrivates, methods=['GET'], defaults={'condition':None})
app.add_url_rule('/datasets/indexPrivates/<int:page>&<condition>', 'datasets_index_privates', datasets.indexPrivates, methods=['GET'])


app.add_url_rule('/datasets/show/<int:Bid>', 'datasets_show', datasets.show, methods=['GET'])
app.add_url_rule('/datasets/show/', 'dataset_edit_share', datasets.editShare, methods=['POST'])



#PROFILE
app.add_url_rule('/profile', 'profile', profile.get_my_profile)
app.add_url_rule('/profile/addInstitute', 'addInstitute', profile.addInstitute, methods=['POST'])

