from flask import Flask, render_template, request, redirect, session, g
import config
import sqlite3
import requests
import json as simplejson
app = Flask(__name__)

@app.before_request
def before_request():
	g.db = sqlite3.connect("budget.db")
	g.db.execute("CREATE TABLE IF NOT EXISTS sources (sourcename VARCHAR, amount INTEGER, sourcecurrency VARCHAR, sourcetype)")

@app.teardown_request
def teardown_request(exception):
	if hasattr(g, 'db'):
		g.db.close()

@app.route('/')
def hello():
	return render_template('index.html')

@app.route('/sources/create', methods = ['GET', 'POST'])
def submit():
	if request.method == 'POST':
		sourcename = request.form['sourcename']
		amount = request.form['amount']
		sourcecurrency = request.form['sourcecurrency']
		sourcetype = request.form['sourcetype']
		g.db.execute("INSERT INTO sources VALUES (?, ?, ?, ?)", [sourcename, amount, sourcecurrency, sourcetype])
		g.db.commit()
		return redirect ('/sources')
	return render_template('source_create.html')

@app.route('/sources/edit', methods = ['GET', 'POST'])
def edit():
	sources = g.db.execute("SELECT * FROM sources").fetchall()
	if request.method == 'POST':
		alldata = request.form.getlist('amount')
		sourcenames = request.form.getlist('source_name')
		for i, item in enumerate(alldata):
			g.db.execute('''UPDATE sources SET amount = ? WHERE sourcename = ? ''', [item, sourcenames[i]])
		g.db.commit()
		return redirect ('/sources')
	return render_template('source_edit.html', **locals())

@app.route('/sources')
def sources():
	sources = g.db.execute("SELECT * FROM sources").fetchall()
	euros = g.db.execute("SELECT amount FROM sources WHERE sourcecurrency == 'EUR'").fetchall()
	usds = g.db.execute("SELECT amount FROM sources WHERE sourcecurrency == 'USD'").fetchall()

	eurSum = sum([i[0] for i in euros])
	#print(eurSum)
	usdSum = sum([i[0] for i in usds])

	response = requests.get('http://data.fixer.io/api/latest?access_key='+config.fixerio_access_key+'&symbols=USD')
	response = response.text
	#print(response)
	data = simplejson.loads(response)
	exchangeRate = data['rates']['USD']
	#print(exchangeRate)

	grandTotal = (eurSum*exchangeRate)+usdSum

	return render_template('sources.html', **locals())

if __name__ == '__main__':
    app.run()