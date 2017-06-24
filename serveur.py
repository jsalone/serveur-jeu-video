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
	db.select ("INSERT INTO magasin(MagasinPosX, MagasinPosY,idJoueur) VALUES (%(posX)s,%(posY)s,%(idJoueur)s) RETURNING idMagasin as magasin", {"posX" : random.randrange(10),"posY" : random.randrange(10),"idJoueur": result[0]['idjoueur']})
	
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
    global json_table
    if request.method == "GET":
        return "OK:GET_METROLOGY"
    elif request.method == "POST":
        return "OK:POST_METROLOGY"

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
    classementJoueur = db.select("SELECT idJoueur,JoueurNom FROM joueur WHERE JoueurNom = %(name)s ORDER BY JoueurBudget",{"name" : playerName})
    availableIngredients['classementJoueur']=classementJoueur
    pan = db.select("SELECT * FROM panneau WHERE idJoueur = %(idjou)s",{"idjou" : monjoueur[0]['idjoueur']})
    mag = db.select("SELECT * FROM magasin WHERE idJoueur = %(idjou)s",{"idjou" : monjoueur[0]['idjoueur']})
    nbpan=len(pan)

    if nbpan!= 0:
	#parti panneau
	mapItem['location']={}
	for matable in pan:
		mapItem['kind'][matable]= 'at'
		mapItem['owner'][matable]= playerName
		mapItem['location'][matable]['latitude']=pan[matable]['PanneauPosY']
		mapItem['location'][matable]['longitude']= pan[matable]['PanneauPosX']
		mapItem['influene'][matable]=pan[matable]['PanneauInfluence']
	#partie mag
	mapItem['kind'][nbpan+1]= 'stand'
	mapItem['owner'][nbpan+1]= playerName	
	mapItem['location'][nbpan+1]['latitude']=mag[nbpan+1]['MagasinPosY']
	mapItem['location'][nbpan+1]['longitude']= mag[nbpan+1]['MagasinPosX']
	mapItem['influene'][nbpan+1]=mag[nbpan+1]['MagasinInfluence']
    else:
	mapItem['kind']= 'stand'
	mapItem['owner']= playerName
	mapItem['location']={}
	mapItem['location']['latitude']=mag[0]['MagasinPosY']
	mapItem['location']['longitude']= mag[0]['MagasinPosX']
	mapItem['influene']=mag[0]['MagasinInfluence']
    availableIngredients['mapItem']=mapItem

    return jsonResponse(availableIngredients)

#availableIngredients:
#	region : 
#		center :
#			
#			latitude float
#			longitude float
#		span :
#			
#			latitudeSpan float
#			longitudeSpan float
#	ranking: string id/name all player
#	itemsByPlayer:{
#		mapItem: repeated pour tous les joueurs
#			kind :string stand ou at
#			owner : string playername
#			location :
#				
#				latitude
#				longitude
#			influence : float distance
#		}
#	ingredient :
#		name string
#		cost float
#		hasAlcohol bool
#		isCold bool
#map:
#	itemsByPlayer:{
#		mapItem: repeated pour tous les joueurs
#			kind :string stand ou at
#			owner : string playername
#			location :
#				
#				latitude
#				longitude
#			influence : float distance
#		}
#playerInfo:
#	playerInfo: repeated pour tous les joueurs
#		cash: float
#		sales: int nombre de vendu par recettes
#		profit : float -> negatif perdu
#		drinksOffered:
#			
#			name
#			price
#			has alcohol
#			is cold
#	}

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
