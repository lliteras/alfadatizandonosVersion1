from flask import redirect, render_template, request, url_for, session, abort, flash, jsonify
from db import get_db
from resources.visualization import bar_plot, line_plot
from models.user import User
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bokeh.plotting import figure, output_file, show
from bokeh.models.tools import HoverTool
import pandas as pd
from bokeh.models import ColumnDataSource, Div, Select, Slider, TextInput
from bokeh.io import curdoc
from bokeh.resources import INLINE
from bokeh.embed import components
from flask_session import Session
from models.establishment import Establishment
from werkzeug.security import generate_password_hash, check_password_hash
import re
 
# Make a regular expression
# for validating an Email
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def index():    
    return render_template('home/dragAndDrop.html')


def login_form():
    return render_template('user/login_form.html')

def show_register():
    provincias = Establishment.select_provinces()
    return render_template('user/register_form.html', provincias=provincias)

def register_form():
    return redirect('/showRegister')

def forgotPassword():
    return render_template('user/forgot_password_form.html')

def login():
    if request.form['submit'] == 'login':
        if 'name' in request.form and 'password' in request.form:
            name = request.form['name']
            password = request.form['password']
            result = User.login(name, name)
            if result and check_password_hash(result[0]['password'], password):
                aux = result[0]
                session['username'] = aux['username']
                session['name'] = aux['name']
                session['email'] = aux['email']
                session['id'] = aux[1]
                session['actualRole'] = result[0]['rolename']
                lista_roles = []
                for res in result:
                    lista_roles.append(res['rolename'])
                session['roles'] = lista_roles
                a = session['roles']
                return index()    

            else:
                return render_template('user/login_form.html', error="Usuario y/o contraseña incorrectos")
    elif request.form['submit'] == 'register':
        return register_form()

def user_exist(username):
    if 'professor' in session['roles']:
        result = User.user_or_email_exist(username)
        if result:
            return jsonify(result = result['id'])
        return jsonify(result = -1)
    return redirect(url_for('home'))


def logout():
    session.clear()
    return redirect(url_for("loginForm"))

def register():
    provincias = Establishment.select_provinces()
    if 'email' in request.form and 'username' in request.form and 'password' in request.form and 'password_repeat' in request.form and 'provinceFormControlSelect' in request.form and 'cityFormControlSelect' in request.form and 'instituteFormControlSelect' in request.form and 'name' in request.form and 'surname' in request.form and 'birthday' in request.form:
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        password_repeat = request.form['password_repeat']
        province = request.form['provinceFormControlSelect']
        city = request.form['cityFormControlSelect']
        institute = request.form['instituteFormControlSelect']
        name = request.form['name']
        surname = request.form['surname']
        birthday = request.form['birthday']
    else:
        return render_template('user/register_form.html', emptyField="Debe completar todos los campos.", email=email, username=username, name=name, surname=surname, birthday=birthday, provincias=provincias)
    if User.emailExist(email):
        return render_template('user/register_form.html', emailExist="El email ya está en uso.", username=username, name=name, surname=surname, birthday=birthday, provincias=provincias)
    if User.usernameExist(username):
        return render_template('user/register_form.html', usernameExist="El nombre de usuario ya está en uso.", email=email, name=name, surname=surname, birthday=birthday, provincias=provincias)
    if username=="" or password=="" or name=="" or surname=="" or email == "" or birthday =="" or city=="" or province=="":
        return render_template('user/register_form.html', emptyField="Debe completar todos los campos.", email=email, username=username, name=name, surname=surname, birthday=birthday, provincias=provincias)
    if len(password)<8:
        return render_template('user/register_form.html', passwordLengthError = "La contraseña debe tener 8 caracteres o más.", email=email, username=username, name=name, surname=surname, birthday=birthday, provincias=provincias)
    if not password == password_repeat:
        return render_template('user/register_form.html', passwordsNoMatch = "Las contraseñas deben coincidir.", email=email, username=username, name=name, surname=surname, birthday=birthday, provincias=provincias)
    password = generate_password_hash(password)
    if not (re.fullmatch(regex,email)):
        return render_template('user/register_form.html', incorrectEmail = "No es un email válido.", username=username, name=name, surname=surname, birthday=birthday, provincias=provincias) 
    eight_years_ago = datetime.now() - relativedelta(years=8)
    birthday = datetime.strptime(birthday, '%Y-%m-%d')
    if birthday>eight_years_ago:
        return render_template('user/register_form.html', incorrectDate = "Seleccione una fecha válida.", email=email, username=username, name=name, surname=surname, provincias=provincias)
    User.register(username, password, province, city, institute, email, name, surname, birthday)
    return render_template('user/login_form.html', registerSuccess="Registro exitoso!")

def changeActualRole(rolename):
    session['actualRole'] = rolename
    return redirect(url_for('home'))
