#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request
from flask import render_template
from db import Db # voyez db.py


import json
import random
import os
import psycopg2
import urlparse

app = Flask(__name__)
app.debug = True

invite=0
debutpartie=0

dfn=0

weathertoday='sunny'
weathertomor='sunny'
timestamp=0

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/reset')
def route_dbinit():
  """Cette route sert à initialiser (ou nettoyer) la base de données."""
  db = Db()
  db.executeFile("database_reset.sql")
  db.close()
  return "Done."

##########################################################################################################################################
# Fonction de réponse
def jsonResponse(data, status=200):
  return json.dumps(data), status, {'Content-Type': 'application/json'}


##########################################################################################################################################
# Requête R8 - Reset
#@app.route("/reset", methods=["GET"])
#def reset():
#    #return json.dumps(json_table[len(json_table)-1])
#    return "OK:RESET"


##########################################################################################################################################
# Requête R4 - Rejoindre une partie
@app.route("/players", methods=["POST"])
def addPlayer():
    print("--------------------------------------rejoindre partie---------------------------------------------------")
    global invite
    db = Db()
    get_json = request.get_json()
    table={}
    if 'name' in get_json:
        table['name'] = get_json['name']
        result = db.select("SELECT * FROM joueur WHERE JoueurNom = %(name)s",{
		"name" : table["name"]
		})
	partiExist = db.select("SELECT idPartie FROM partie")
	taille = len(partiExist)
	if taille == 0:
		partiExist=db.select ("INSERT INTO partie(PartieNom) VALUES (%(name)s) RETURNING idPartie",{"name" : table["name"]})
	taille = len(result)
	if taille!= 0:
		
		
		while taille !=0:
			invite+=1
			table['name'] = "invite%d"% invite
			result = db.select("SELECT * FROM joueur WHERE JoueurNom = %(name)s",{"name" : table["name"]})
			taille = len(result)
					
	
	idjoueur=db.select ("INSERT INTO joueur(JoueurNom, JoueurBudget,IdPartie) VALUES (%(name)s, 50,%(parti)s) RETURNING idJoueur", {"name" : table["name"],"parti":partiExist[0]['idpartie']})
	result = db.select("SELECT idJoueur FROM joueur WHERE JoueurNom = %(name)s",{
		"name" : table["name"]
		})
	db.select ("INSERT INTO magasin(MagasinPosX, MagasinPosY,idJoueur,MagasinInfluence) VALUES (%(posX)s,%(posY)s,%(idJoueur)s,1) RETURNING idMagasin as magasin", {"posX" : random.randrange(10),"posY" : random.randrange(10),"idJoueur": result[0]['idjoueur']})
	
	result = db.select("SELECT * FROM magasin WHERE idJoueur = %(name)s",{
		"name" : result[0]['idjoueur']
		})
    db.close()
    table['location'] = {}
    table['location']['latitude'] = result[0]['magasinposy']
    table['location']['longitude'] = result[0]['magasinposx']
    table['info'] = {}
    table['info']['cash'] = 50
    table['info']['sales'] = 0
    table['info']['profit'] = 0.0

    return jsonResponse(table)

##########################################################################################################################################
# Requête R4 - Quitter une partie
@app.route("/players/<playerName>", methods=["DELETE"])
def deletePlayer(playerName):
    print("-----------------------------------------delete----------------------------------------------------------")
    db = Db()
    result = db.select("SELECT idJoueur FROM joueur WHERE JoueurNom = %(name)s",{"name" : playerName})
    magasin=db.select("SELECT * FROM magasin WHERE idJoueur = %(name)s",{"name" : result[0]['idjoueur']})
    panneau=db.select("SELECT * FROM panneau WHERE idJoueur = %(name)s",{"name" : result[0]['idjoueur']})

    recette=db.select("SELECT * FROM recette WHERE idJoueur = %(name)s",{"name" : result[0]['idjoueur']})
    
    taille = len(recette)
    if taille !=0:
	db.execute("DELETE FROM recette WHERE idJoueur = %s",result[0]['idjoueur']) 
    	contenir=db.select("SELECT * FROM contenir WHERE idRecette = %(name)s",{"name" : recette[0]['idRecette']})
	taille = len(contenir)
	if taille !=0: 
		db.execute("DELETE FROM contenir WHERE idJoueur = %s",recette[0]['idrecette'])  

    db.execute("DELETE FROM magasin WHERE idJoueur = "+ str(result[0]['idjoueur'])) 
    db.execute("DELETE FROM joueur WHERE idJoueur = "+ str(result[0]['idjoueur'])) 
    db.close()
    #if (playerName == ""):
    return "OK:DELETE " + playerName


##########################################################################################################################################
# Requête R1/R7 - Metrology
@app.route("/metrology", methods=["GET", "POST"])
def metrology():
    global dfn
    global weathertoday
    global weathertomor
    global timestamp
    if request.method == "GET":
	print("-----------------------------------------GET METRO----------------------------------------------------------")
	weather={}
	forcast={}
	Temps={}
	forcast['dfn']={}
	forcast['weather']={}
	forcast['dfn'][0]=0
	forcast['weather'][0]=weathertoday
	forcast['dfn'][1]=1
	forcast['weather'][1]=weathertomor
	weather['forcast']=forcast
	Temps['timestamp']=timestamp
	Temps['weather']=weather
        return jsonResponse(Temps)
    elif request.method == "POST":
	get_json = request.get_json()
	timestamp=get_json['timestamp']
	day=get_json['weather']['forcast'][0]['dfn']
	if day==0:
		weathertoday=get_json['weather']['forcast'][0]['weather']
		weathertomor=get_json['weather']['forcast'][1]['weather']
	else :
		weathertoday=get_json['weather']['forcast'][1]['weather']
		weathertomor=get_json['weather']['forcast'][0]['weather']		
	print("-----------------------------------------POST METRO----------------------------------------------------------")
        return "OK:POST_METROLOGY"
#timestamp: int nb d'heure joue 0 aujourd'hui 1 demain
#weather:
#	forcast: // 2 forcast pour aujourd'hui et demain
#		dfn : int day from now - 0 aujourd'hui 1 demain
#		weather:
    #return json.dumps(json_table), 200, {'Content-Type': 'application/json'}


##########################################################################################################################################
# Requête R3 - Sales
@app.route("/sales", methods=["POST"])
def sales():
    print("-----------------------------------------sales----------------------------------------------------------")
    global json_table
    table={}
    #player: string
    #item : string
    #quantity
    db = Db()
    get_json = request.get_json()
    if 'player' in get_json:
	table['name'] = get_json['player']
	table['item'] = get_json['item']
	table['quantity'] = get_json['quantity']
        idjou = db.select("SELECT idJoueur FROM joueur WHERE JoueurNom = %(name)s",{
		"name" : table["name"]
		})
	idrec = db.select("SELECT idRecette FROM recette WHERE RecetteNom = %(name)s",{
		"name" : table["item"]
		})
	vend =db.select("SELECT * FROM avoir WHERE idJoueur = %(name)s AND idRecette = %(idrec)s",{
		"name" : idjou[0]["idjoueur"],"idrec" : idrec[0]["idrecette"]
		})
	taille = len(vend)
	if taille!= 0:
		vend[0]['vendre']+=table["quantity"]
		db.execute("UPDATE avoir SET vendre=(%(vendre)s) WHERE idJoueur=(%(j_user)s)AND idRecette = %(namerec)s", {"vendre": vend[0]["vendre"],"j_user" : idjou[0]["idjoueur"],"namerec" : idrec[0]["idrecette"]})
	else:
		idjoueur = db.select ("INSERT INTO vendre(vendre, idJoueur, idRecette) VALUES (%(vendre)s,%(idjoueur)s ,%(idrec)s) RETURNING idJoueur", {"vendre" : table["quantity"],"idjoueur" : idjou[0]["idjoueur"],"idrec" : idrec[0]["idrecette"] })

    #json_table[value].update(get_json)
    db.close()

    return "OK:POST_SALES"


##########################################################################################################################################
# Requête R6 - Instructions du joueur
@app.route("/actions/<playerName>", methods=["POST"])
def actionsPlayer(playerName):

#action:
#	
    #global json_table
    #return json.dumps(json_table[value])
    return "OK:POST_" + playerName


##########################################################################################################################################
# Requête R2 -  Map
@app.route("/map", methods=["GET"])
def map():

    #return json.dumps(json_table)
    return "OK:GET_MAP"
#map:
#	region : 
#		center :
#			coordinates :
#				latitude
#				longitude
#		span :
#			coordinatesSpan :
#				latitudeSpan
#				longitudeSpan	
#	ranking: string id/name all player
#	itemsByPlayer:{
#		mapItem: repeated pour tous les joueurs
#			kind :string stand ou at
#			owner : string playername
#			location :
#				coordinates :
#					latitude
#					longitude
#			influence : float distance
#		}
#	playerInfo:{
#		playerInfo: repeated pour tous les joueurs
#			cash: float
#			sales: int nombre de vendu par recettes
#			profit : float -> negatif perdu
#			drinksOffered:
#				drinkInfo :
#					name
#					price
#					has alcohol
#					is cold
#		}
#	drinksByPlayer:{
#		drinkInfo :
#			name
#			price
#			has alcohol
#			is cold
#		}

##########################################################################################################################################
# Requête R5 - Détails d'une partie
@app.route("/map/<playerName>", methods=["GET"])
def mapPlayer(playerName):
    db = Db()
    table ={}
    availableIngredients={}
    mapItem= {}
    location={}
    monjoueur = db.select("SELECT * FROM joueur WHERE JoueurNom = %(name)s",{"name" : playerName})
    pan = db.select("SELECT * FROM panneau WHERE idJoueur = %(idjou)s",{"idjou" : monjoueur[0]['idjoueur']})
    mag = db.select("SELECT * FROM magasin WHERE idJoueur = %(idjou)s",{"idjou" : monjoueur[0]['idjoueur']})
    nbpan=len(pan)

    #ingredient
    mesingredient= db.select("SELECT * FROM ingredient")
    ingredient={}
    ingredient['name']={}
    ingredient['cost']={}
    ingredient['hasAlcohol']={}
    ingredient['isCold']={}
    for dep in range(len(mesingredient)):
	ingredient['name'][dep]=mesingredient[dep]['ingredientnom']
	ingredient['cost'][dep]=mesingredient[dep]['ingredientprix']
	ingredient['hasAlcohol'][dep]=mesingredient[dep]['ingredientalcool']
	ingredient['isCold'][dep]=mesingredient[dep]['ingredienttemperature']

    availableIngredients['availableIngredients']=ingredient
    #map
    mamap={}

    #region
    ###############################################################
    # a faire
    #
    ###############################################################
    #ranking
    mamap['ranking']=db.select("SELECT idJoueur,JoueurNom FROM joueur WHERE JoueurNom = %(name)s ORDER BY JoueurBudget",{"name" : playerName})
    #itemsduPlayer
    if nbpan!= 0:
	#parti panneau
	mapItem['location']={}
	for matable in range(len(pan)):
		mapItem['kind'][matable]= 'at'
		mapItem['owner'][matable]= playerName
		mapItem['location'][matable]['latitude']=pan[matable]['panneauposy']
		mapItem['location'][matable]['longitude']= pan[matable]['panneauposx']
		mapItem['influene'][matable]=pan[matable]['panneauinfluence']
	#partie mag
	mapItem['kind'][nbpan+1]= 'stand'
	mapItem['owner'][nbpan+1]= playerName	
	mapItem['location'][nbpan+1]['latitude']=mag[nbpan+1]['magasinposy']
	mapItem['location'][nbpan+1]['longitude']= mag[nbpan+1]['magasinposx']
	mapItem['influene'][nbpan+1]=mag[nbpan+1]['magasininfluence']
    else:
	mapItem['kind']= 'stand'
	mapItem['owner']= playerName
	mapItem['location']={}
	mapItem['location']['latitude']=mag[0]['magasinposy']
	mapItem['location']['longitude']= mag[0]['magasinposx']
	mapItem['influence']=mag[0]['magasininfluence']
    
    mamap['itemsByPlayer']=mapItem
    availableIngredients['map']=mamap

    #playerInfo
    playerInfo={}
    playerInfo['cash']=monjoueur[0]['joueurbudget']
    sales={}
    idrecette=recette=db.select("SELECT * FROM recette")
    compvendu={}
    for dep in range(len(idrecette)):
	compvendu[dep]=db.select("SELECT vendre FROM avoir WHERE idJoueur = %(idjou)s AND idRecette=%(idrec)s ",{"idjou" : monjoueur[0]['idjoueur'], "idrec" : idrecette[0]['idrecette']})
    
    vendu=0
    for dep in range(len(idrecette))
	vendu+=compvendu[dep]
	
#playerInfo:
#	cash: float
#	sales: int nombre de vendu
#	profit : float -> negatif perdu
#	drinksOffered:
#		name
#		price
#		has alcohol
#		is cold
#	}

    return jsonResponse(availableIngredients)

#availableIngredients:
#		name string
#		cost float
#		hasAlcohol bool
#		isCold bool	
#map:
#	region:
#		center:
#			latitude : float
#			longitude : float
#		span:
#			latitudeSpan : float
#			longitudeSpan : float
#
#	ranking: string
#	itemsByPlayer :
#		mapItem :
#			kind: string stand or ad
#			owner: string
#			location :
#				latitude : float
#				longitude : float
#			influence : float


##########################################################################################################################################
# Requête R9 - Liste ingrédients
@app.route("/ingredients", methods=["GET"])
def ingredients():
    print("-----------------------------------------ingredients----------------------------------------------------------")
    db = Db()
    table={}
    result = db.select("SELECT * FROM ingredient")
    #print(result)
    table['ingredients'] = result
    db.close()
    return jsonResponse(table)




if __name__ == "__main__":
    app.run()
