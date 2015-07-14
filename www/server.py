import os
import ConfigParser
import requests
from bson.json_util import dumps
from bson.objectid import ObjectId
from bson import BSON
from bson import json_util
from flask import Flask,render_template,request
from pymongo import MongoClient 
from random import randint
from datetime import datetime
import json


app = Flask(__name__)
app.debug = True


# constants
CONFIG_FILENAME = 'app.config'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FORMAT = []
DATA_FORMAT.append({})
DATA_FORMAT[0]["Error"] = "YOUR DATA SHOULD LOOK LIKE THIS"
DATA_FORMAT.append({})
DATA_FORMAT[1]["device_id"] = "1"
DATA_FORMAT[1]["unix_epoch"] = "1436807393"
DATA_FORMAT[1]["human_date"] = "2015-07-03 22:02:34"
DATA_FORMAT[1]["temp_c"] = 10.4
DATA_FORMAT[1]["temp_f"] = 60.5
DATA_FORMAT[1]["conductivity_raw"] = 310


# read in app config
config = ConfigParser.ConfigParser()
config.read(os.path.join(BASE_DIR,CONFIG_FILENAME))

# MongoDB & links to each collection
#uri = "mongodb://"+ config.get('db','user')+ ":"+ config.get('db','pass')+"@" +config.get('db','host') + ":" + config.get('db','port')+"/?authSource="+config.get('db','auth_db')

#LOCAL DEVELOPMENT
#uri = "mongodb://"+config.get('db','host')+":"+ config.get('db','port')

#CLOUD9 DEVELOPMENT
uri = "mongodb://"+ os.environ["IP"] +":"+ config.get('db','port')

db_client = MongoClient(uri)
app.db = db_client[config.get('db','name')]
app.db_waterdata_collection = app.db[config.get('db','waterdata_collection')]

@app.route('/')
def hello_world():
    return render_template('index.html')


# Saves sensor data posted to the DB, make sure you send with Content-Type: json
@app.route('/saveSingleObservation', methods=['GET', 'POST'])
def save_sensor_data():
	observation = request.get_json()
	if observation is not None:
		save_single_observation(observation)
		return "OK"
	else:
		return json.dumps(DATA_FORMAT, sort_keys=True, indent=4, default=json_util.default)

def save_single_observation(observation):
	if observation is not None:
		observation["mongo_datetime"] = datetime.fromtimestamp(observation["unix_epoch"])
		app.db.waterdata_collection.insert(observation)
	
@app.route('/saveMultipleObservations', methods=['GET', 'POST'])
def save_multiple_sensor_data():
	content = request.get_json()
	if content is not None:
		for observation in content:
			save_single_observation(observation)
		return "OK"
	else:
		return json.dumps(DATA_FORMAT, sort_keys=True, indent=4, default=json_util.default)

# JSON data dump based on parameter OR parameters of interest
# create list 
# visualize a parameter of interest
# pull all of those and graph them with googlecharts
# return timestamp and list of parameters, 1-n, that have TEMP AND HUMIDITY
@app.route('/dataDump', methods=['GET', 'POST'])
def datadump():
	result=[]
	listOfParams = request.args.get("listOfParams")
	sort = request.args.get("sort")
	if sort is None:
		sort = -1
	else:
		sort = int(sort)
	if listOfParams is None:
		return "ERROR: Send me something like this: http://127.0.0.1:5000/dataDump?listOfParams=conductivity_raw,temp_c&sort=1"
	else: 
		listOfParams = listOfParams.split(",")
		result = getData(listOfParams, sort)
	return json.dumps(result, sort_keys=True, indent=4, default=json_util.default)

# pull out data we want to  see
# format it for google
# send to google
# print response 
# google charts and print out a grid of temp, conductivity etc over the last x period of time
@app.route('/visualize', methods=['GET', 'POST'])
def visualize():
	
	data=[]
	sort = request.args.get("sort")
	if sort is None:
		sort = -1
	else:
		sort = int(sort)
	listOfParams = request.args.get("listOfParams")
	if listOfParams is None:
		return "ERROR: Send me some data in the listOfParams variable" 

	listOfParams = listOfParams.split(",")
	firstThing = listOfParams[0]
	data = getData(listOfParams, sort)
	title = firstThing

	return render_template('chart.html', title=title, data=json.dumps(data, sort_keys=True, indent=None, default=json_util.default))

#accepts a list of parameters and then retrieves all records that have those parameters in the DB
def getData(listOfParams, sort):
	result=[]

	query = []
	query.append({"mongo_datetime" : {'$exists':'true'} })
	fieldList = {}	
	fieldList["mongo_datetime"]=1
	
	for item in listOfParams:
		query.append({item : {'$exists':'true'} })
		fieldList[item]= 1

	print fieldList	
	q = app.db.waterdata_collection.find({'$and': query}, fieldList).sort([("mongo_datetime",sort)])
	for row in q:
		result.append(row)
	return result

if __name__ == '__main__':
    app.run( host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)) )























