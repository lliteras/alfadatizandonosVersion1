import tweepy
import json
from collections import Counter
from itertools import chain
from flask import redirect, render_template, request, url_for, session, abort, flash, jsonify
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.models.tools import HoverTool, BoxZoomTool, ResetTool, TapTool
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges, EdgesAndLinkedNodes
import math
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.models import GraphRenderer, StaticLayoutProvider, Oval, Circle, MultiLine, Label, LabelSet, ColumnDataSource
from bokeh.palettes import Spectral8
#Importing Libraries
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
#Importing Dataset
import base64, re
from io import BytesIO
from bokeh.io import export_png
from bokeh.io.export import get_screenshot_as_png
from selenium import webdriver


def word_cloud(text):
	# Creating word_cloud with text as argument in .generate() method
	wordcloud = WordCloud(collocations = False, background_color = 'white',width=1600, height=800).generate(text)
	# Display the generated Word Cloud
	wordcloud = wordcloud.to_image()
	buffered = BytesIO()
	wordcloud.save(buffered, format = "JPEG")
	img_byte = buffered.getvalue() # bytes
	img_base64 = base64.b64encode(img_byte).decode('ascii')
 #Base64 - encoded bytes * not str
	return img_base64


def twitter_search(noNav):

	noNavBool = False

	if noNav ==1:

		noNavBool = True

	return render_template('home/twitterSearch.html', noNav=noNavBool)


preposiciones = ['a', 'al', 'ante', 'bajo', 'cabe', 'con', 'contra', 'de', 'del', 'desde', 'durante', 'en', 'entre', 'hacia', 'hasta', 'mediante', 'para', 'por', 'según', 'sin', 'so', 'sobre', 'tras', 'versus', 'vía']
articulos = ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas']
pronombres = ['yo', 'me', 'mi', 'conmigo', 'tu', 'te', 'ti', 'contigo', 'usted', 'vos', 'él', 'lo', 'le', 'se', 'sí', 'consigo', 'ella', 'la', 'ello', 'lo', 'nosotros', 'nos', 'nosotras', 'vosotros', 'vosotras', 'os', 'ustedes', 'ellos', 'ellas', 'los', 'las', 'les', 'consigo', 'su', 'eso','esa', 'esas', 'esos', 'esta', 'este','esto','estas','estos','aquel','aquella','aquellos','aquellas']
conjunciones = ['y', 'que', 'qué', 'q', 'e', 'ni', 'o', 'ya sea', 'pero', 'mas', 'sino', 'sin embargo', 'luego', 'pues', 'con que', 'asi', 'porque', 'puesto que',  'ya que', 'pues si', 'con tal que', 'siempre que', 'al menos que', 'como', 'por', 'que']
adverbios = ['asi', 'así', 'ahora', 'antes', 'despues', 'ayer', 'hoy', 'mañana', 'mas','más','temprano', 'todavia', 'ya', 'pronto', 'tarde', 'aqui', 'aca', 'alli', 'ahi', 'alla', 'cerca', 'lejos', 'dentro', 'fuera', 'alrededor', 'encima', 'detras', 'delante', 'despacio', 'deprisa', 'bien', 'mal', 'mucho', 'poco', 'muy', 'casi', 'todo', 'nada', 'algo', 'medio', 'demasiado', 'bastante', 'mas', 'menos', 'ademas', 'incluso', 'tambien', 'si', 'no', 'tampoco', 'jamas', 'nunca', 'acaso', 'quiza', 'quizas', 'tal vez', 'a lo mejor']
specialCharacters = "\'#!?,.;-|"
verbo_ser = ['ser', 'soy', 'eres', 'sos', 'es', 'somos', 'son', 'sois', 'sido', 'era', 'eras', 'eramos', 'eramos', 'erais', 'eran', 'fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron', 'sere', 'seré', 'sere', 'seras','serás','serán', 'seran', 'seremos','seréis', 'sería', 'seria','serías', 'serias','sería', 'seriamos', 'serían','serian']
verbo_estar = ['estar','estoy', 'estás', 'estas', 'esta', 'está', 'estan', 'están', 'estamos', 'estaís', 'estais', 'estado', 'estaba', 'estabas', 'estaba', 'estábamos', 'estabais', 'estaban', 'estuve', 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron', 'estaré', 'estare', 'estarás', 'estaras', 'estará', 'estara']
verbo_haber = ['haber','he', 'has', 'ha', 'hemos', 'han', 'habeis', 'habéis', 'han', 'habido', 'había', 'habia', 'habias', 'habías', 'habian', 'habían', 'habiamos', 'habíamos', 'habiais', 'habíais', 'hube', 'hubiste', 'hubo', 'hubimos', 'hubisteis', 'hubieron', 'habré', 'habre', 'habrás', 'habrá', 'habra', 'habremos', 'habréis', 'habrán', 'habran', 'habría', 'habria','habrias','habrías', 'habría', 'habria', 'habríamos', 'habriamos', 'habríais', 'habriais', 'habrían', 'habrian']
verbo_tener = ['tener','tengo', 'tienes', 'tiene', 'tenes', 'tenemos', 'tenéis', 'teneis', 'tienen', 'tenia', 'tenía', 'tenías', 'tenias', 'teniamos', 'teniais', 'tenian', 'tenían', 'tuve', 'tuviste', 'tuvo', 'tuvimos', 'tuvieron', 'tuviste', 'tuvisteis', 'tendré', 'tendre', 'tendrás', 'tendras', 'tendrá', 'tendra', 'tendremos', 'tendreis', 'tendrán', 'tuvido']

def api_twitter_search(stringToSearch, topQuantity, articles, prep, pron, conj, adv, verbos, links):

	wordsToExclude = []

	if articles == 1:
		wordsToExclude = wordsToExclude + articulos

	if prep == 1:
		wordsToExclude = wordsToExclude + preposiciones

	if pron == 1:
		wordsToExclude = wordsToExclude + pronombres

	if conj == 1:
		wordsToExclude = wordsToExclude + conjunciones

	if adv == 1:
		wordsToExclude = wordsToExclude + adverbios

	if verbos == 1:
		wordsToExclude = wordsToExclude + verbo_estar + verbo_tener + verbo_haber + verbo_ser



	consumer_key="YXA1EA48NTgTWFKeL4ENYdmVl"
	consumer_secret="OpiF2c0NmhqAT7wX6rJZVGs777hHQv3KI3UkyNwBHElC4H2PDi"
	access_token="592381377-xQM7VleetCSVhDA7dUC7ZY3CIRc25TXdHqUyTsal"
	access_token_secret="SniNAifJIoNg3b0wOCbf5Hi6pAyuihFPnp2fx3N9V85gD"

	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

	auth.set_access_token(access_token, access_token_secret)

	api = tweepy.API(auth, wait_on_rate_limit=True)

	tweet_list = []

	counter = Counter()
	counterByWord = {}

	text = ""
	
	for tweet in tweepy.Cursor(api.search_tweets, q= (stringToSearch + ' -filter:retweets'), lang='es', tweet_mode='extended').items(100):


		tweetTextAux = tweet.full_text.replace("\n", "").lower()

		if links == 1:
			tweetTextAux = re.sub(r'http\S+', '', tweetTextAux)

		for x in range(len(specialCharacters)):
			tweetTextAux = tweetTextAux.replace(specialCharacters[x],"")

		text += tweet.full_text

		tweetTextAux = tweetTextAux.split()

		auxCounter = Counter(tweetTextAux)

		counter.update(auxCounter)
		
		for word in tweetTextAux:
			if word not in counterByWord:
				counterByWord[word] = Counter()
			counterByWord[word].update(auxCounter)

	wordsToPop = []

	for x in counter.keys():
		if x in wordsToExclude:
			wordsToPop.append(x)

	for x in wordsToPop:
		counter.pop(x, None)

	querywords = text.split()
	resultwords  = [word for word in querywords if word.lower() not in wordsToExclude]
	text = ' '.join(resultwords)
	
	if links == 1:
		text = re.sub(r'http\S+', '', text)
	
	mostCommons = counter.most_common(topQuantity)
	relations = []
	relations2 = []
	relationsStart = []
	relationsEnd = []
	for i in range(topQuantity):
		
		relations.append([])


		for j in range(topQuantity):
			


			if i == j:

				
				relations[i].append(0)
				break
			
			else:

				quantity = counterByWord[mostCommons[i][0]][mostCommons[j][0]]

				if  quantity != 0:
					relationsStart.append(i)
					relationsEnd.append(j)
					relations2.append(str(quantity))

				relations[i].append(quantity)

	mostCommonWords = [x[0] for x in mostCommons]
	mostCommonWordsQuantities = [x[1] for x in mostCommons]			

	maxCount = max(mostCommonWordsQuantities)
	radio = []

	#put the radio of the circle depending of the count
	for quantity in mostCommonWordsQuantities:

		radio.append((0.18/maxCount)*quantity + 0.1)
		


	node_indices = list(range(topQuantity))

	plot = figure(x_range=(-5.2,5.2), y_range=(-5.2,5.2))

	graph = GraphRenderer()

	graph.node_renderer.data_source.add(node_indices, 'index')
	graph.node_renderer.data_source.add(radio, 'radio')
	graph.node_renderer.data_source.add(mostCommonWords, 'word')
	graph.node_renderer.data_source.add(mostCommonWordsQuantities, 'quantity')
	graph.node_renderer.glyph = Circle(radius='radio')


	graph.edge_renderer.data_source.data = dict(
	    start=relationsStart,
	    end=relationsEnd)

	### start of layout code
	circ = [i*2*math.pi/topQuantity for i in node_indices]
	x = [math.cos(i)*4 for i in circ]
	y = [math.sin(i)*4 for i in circ]

	graph_layout = dict(zip(node_indices, zip(x, y)))
	graph.layout_provider = StaticLayoutProvider(graph_layout=graph_layout)

	graph.node_renderer.glyph = Circle(radius='radio', fill_color=Spectral8[0])
	graph.node_renderer.selection_glyph = Circle(radius='radio', fill_color=Spectral8[2])
	graph.node_renderer.hover_glyph = Circle(radius='radio', fill_color=Spectral8[1])

	graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width=4)
	graph.edge_renderer.selection_glyph = MultiLine(line_color=Spectral8[2], line_width=4)
	graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral8[1], line_width=4)


	graph.selection_policy = NodesAndLinkedEdges()


	graph.inspection_policy = NodesAndLinkedEdges()
	#graph.inspection_policy = EdgesAndLinkedNodes()
	
	node_hover_tool = HoverTool(renderers=[graph.node_renderer],tooltips=[("cantidad", "@quantity"), ("palabra", "@word")], show_arrow = False)
	plot.add_tools(node_hover_tool)

	graph.edge_renderer.data_source.add(relations2, 'cantidad')
	edge_hover_tool = HoverTool(renderers=[graph.edge_renderer],tooltips=[("cantidad de apariciones en el mismo tweet", "@cantidad")], line_policy='interp')
	plot.add_tools(edge_hover_tool)
	plot.add_tools(TapTool())

	"""graph.inspection_policy = EdgesAndLinkedNodes()
				graph.edge_renderer.data_source.add(['word1','word2','word3','word4','word5','word6','word7','word8','word9','word10'], 'word')
				edge_hover_tool = HoverTool(tooltips=[("word", "@word")], show_arrow = False)
				plot.add_tools(edge_hover_tool)"""

	#Labels
	circ2 = [i*2*math.pi/topQuantity for i in node_indices]
	x2 = [(math.cos(i)*4.5)-0.2 for i in circ2]
	y2 = [(math.sin(i)*4.4)-0.15 for i in circ2]			

	source2 = ColumnDataSource(data = dict(x=x2, y=y2, labels=mostCommonWords))

	labels = LabelSet(x='x', y='y', text='labels', source=source2, render_mode='canvas')



	plot.add_layout(labels)
	plot.renderers.append(graph)


	

	from selenium import webdriver
	from webdriver_manager.firefox import GeckoDriverManager
	import os
	os.environ['MOZ_HEADLESS'] = '1'

	driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())


	imageSocialGraph = get_screenshot_as_png(plot, driver=driver)
	buffered = BytesIO()
	imageSocialGraph.save(buffered, format = "PNG")
	img_byte = buffered.getvalue() # bytes
	imgBase64SocialGraph = base64.b64encode(img_byte).decode('ascii')

	script, div = components(plot)

	image = word_cloud(text)

	return render_template(
		'home/twitterGraphAndCloud.html',
		image = image,
		imgBase64SocialGraph=imgBase64SocialGraph,

		plot_script=script,
		plot_div=div,
		js_resources=INLINE.render_js(),
		css_resources=INLINE.render_css(),
	).encode(encoding='UTF-8')

	aa		
