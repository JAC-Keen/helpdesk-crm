from flask import Flask, render_template,request,redirect,url_for # For flask implementation
from pymongo import MongoClient # Database connector
from bson.objectid import ObjectId # For ObjectId to work
from bson.errors import InvalidId # For catching InvalidId exception for ObjectId
import os
import keen

mongodb_host = os.environ.get('MONGO_HOST', 'localhost')
mongodb_port = int(os.environ.get('MONGO_PORT', '27017'))
client = MongoClient(mongodb_host, mongodb_port)    #Configure the connection to the database
db = client.camp2016    #Select the database
todos = db.todo #Select the collection

app = Flask(__name__)
title = "Helpdeskr"
heading = "Helpdesk"
#modify=ObjectId()

keen.project_id = "5dc3034bc9e77c000107cfca"
keen.write_key = "E2F05C8D16FCD419641CAA8B5DDF0CF8666D6A92825EA3649C1C49C17547DE0AA670CF5253A28CB84186931745A8F8C3E6C2765F10336AB1A3C749092E8D4D399A98090F2C5D1A5C6F0C1EC0E6CAF030909C8CE399977FD6728725BF3920749D"

def redirect_url():
	return request.args.get('next') or \
		request.referrer or \
		url_for('index')

@app.route("/list")
def lists ():
	#Display the all Tasks
	todos_l = todos.find()
	a1="active"
	return render_template('index.html',a1=a1,todos=todos_l,t=title,h=heading)

@app.route("/")
@app.route("/uncompleted")
def tasks ():
	#Display the Uncompleted Tasks
	todos_l = todos.find({"done":"no"})
	a2="active"
	return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading)


@app.route("/completed")
def completed ():
	#Display the Completed Tasks
	todos_l = todos.find({"done":"yes"})
	a3="active"
	return render_template('index.html',a3=a3,todos=todos_l,t=title,h=heading)

@app.route("/done")
def done ():
	#Done-or-not ICON
	id=request.values.get("_id")
	task=todos.find({"_id":ObjectId(id)})
	if(task[0]["done"]=="yes"):
		todos.update({"_id":ObjectId(id)}, {"$set": {"done":"no"}})
		# Persisting a completed task with the user_id
		keen.add_event("incompleted",{
			"user_identity": id
		})
	else:
		todos.update({"_id":ObjectId(id)}, {"$set": {"done":"yes"}})
		# Persisting a completed task with the user_id
		keen.add_event("completed",{
			"user_identity": id
		})
	redir=redirect_url()	# Re-directed URL i.e. PREVIOUS URL from where it came into this one

#	if(str(redir)=="http://localhost:5000/search"):
#		redir+="?key="+id+"&refer="+refer

	return redirect(redir)

#@app.route("/add")
#def add():
#	return render_template('add.html',h=heading,t=title)

@app.route("/action", methods=['POST'])
def action ():
	#Adding a Task
	name=request.values.get("name")
	desc=request.values.get("desc")
	date=request.values.get("date")
	pr=request.values.get("pr")
	_id=todos.insert({ "name":name, "desc":desc, "date":date, "pr":pr, "done":"no"})
	print("Sanity Check {0}".format(_id))

	# Add Keen to collect the event and persist a User ID
	keen.add_event("helpdesk_task",{
	  "name": name,
	  "desc": desc,
	  "date": date,
	  "pr": pr,
	  "user_identity": "{0}".format(_id)
	})

	return redirect("/list")

@app.route("/remove")
def remove ():
	#Deleting a Task with various references
	key=request.values.get("_id")
	todos.remove({"_id":ObjectId(key)})
	return redirect("/")

@app.route("/update")
def update ():
	id=request.values.get("_id")
	task=todos.find({"_id":ObjectId(id)})
	return render_template('update.html',tasks=task,h=heading,t=title)

@app.route("/action3", methods=['POST'])
def action3 ():
	#Updating a Task with various references
	name=request.values.get("name")
	desc=request.values.get("desc")
	date=request.values.get("date")
	pr=request.values.get("pr")
	id=request.values.get("_id")
	todos.update({"_id":ObjectId(id)}, {'$set':{ "name":name, "desc":desc, "date":date, "pr":pr }})
	return redirect("/")

@app.route("/search", methods=['GET'])
def search():
	#Searching a Task with various references
	key=request.values.get("key")
	refer=request.values.get("refer")
	if(refer=="id"):
		try:
			todos_l = todos.find({refer:ObjectId(key)})
			if not todos_l:
				return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading,error="No such ObjectId is present")
		except InvalidId as err:
			pass
			return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading,error="Invalid ObjectId format given")
	else:
		todos_l = todos.find({refer:key})
	return render_template('searchlist.html',todos=todos_l,t=title,h=heading)

@app.route("/about")
def about():
	return render_template('credits.html',t=title,h=heading)

if __name__ == "__main__":
	env = os.environ.get('APP_ENV', 'development')
	port = int(os.environ.get('PORT', 5000))
	debug = False if env == 'production' else True
	app.run(host='0.0.0.0', port=port, debug=debug)
	# Careful with the debug mode..
