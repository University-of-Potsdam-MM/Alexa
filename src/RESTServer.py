from flask import Flask, request
import BaseXClient
import requests
import json
import time
import airspeed
from lxml import etree
from LRSClient import LRSClient


app = Flask(__name__)

# config BaseX Database Connection
DB_HOST = "127.0.0.1"
DB_PORT = 1984
DB_USER = "admin"
DB_PASS = "admin"
DB_NAME = "tutordb"

# config recommendation system url
rec_sys_url = "http://localhost:5002"

@app.route('/api/lrs/statement', methods=('POST',))
def apiSendStatementToLRS():
    if request.method == 'POST':
        statement = request.data
        lrs = LRSClient()
        response = lrs.sendStatement(statement)
    return json.dumps(response)


@app.route('/api/contentpackage/<topic>', methods=('POST',))
def apiContentPackage(topic):
    if request.method == 'POST':
        cp = request.data
        response = writeContentPackage(cp, topic)
    return json.dumps(response)


@app.route('/api/item/<file>', methods=('POST',))
def apiItem(file):
    if request.method == 'POST':
        item = request.data
        response = writeItem(file, item)
    return json.dumps(response)


@app.route('/api/topic/titles', methods=('GET',))
def apiTopicTitles():
    if request.method == 'GET':
        response = getTopicTitles()
    return json.dumps(response)


@app.route('/api/recommendation/<name>/<topic>', methods=('GET',))
def apiRecommendation(name, topic):
    if request.method == 'GET':
        response = getRecommendation(name, topic)
    return json.dumps(response)


@app.route('/api/learner/<name>', methods=('GET', 'POST',))
def apiLearner(name):
    if request.method == 'GET':
        response = getLearnerProfile(name)
    if request.method == 'POST':
        response = writeLearnerProfile(name)
    return json.dumps(response)


@app.route('/api/learner/<name>/activity', methods=('GET', 'POST',))
def apiLearnerActivity(name):
    if request.method == 'GET':
        xml = getLearnerProfile(name)
        if xml != "x-none":
            response = getLastActivity(name, xml)
        else:
            response = xml
    if request.method == 'POST':
        activity = request.data
        response = writeActivity(name, activity)
    return json.dumps(response)


# gets topics from all CP in DB by xquery expression
def getTopicTitles():
    session = createDBSession()
    session.execute("open {0}".format(DB_NAME))
    query = session.query("""
		declare namespace imsld = "http://www.imsglobal.org/xsd/imsld_v1p0"; 
		let $doc := collection("{0}/contentpackages")
		return $doc//imsld:learning-design/imsld:title/text()""".format(DB_NAME))
    titles = ""
    for _, item in query.iter():
        titles = titles + item + ". "
    query.close()
    response = titles
    return response

# gets lip of a user by name by xquery expression
def getLearnerProfile(name):
    session = createDBSession()
    session.execute("open {0}".format(DB_NAME))
    query = session.query("""
		declare namespace imslip = "http://www.imsglobal.org/xsd/imslip_v1p0"; 
		let $col := collection("{0}/learnerprofiles") 
		for $doc in $col
			where $doc//*[imslip:typename/imslip:tyvalue = 'First']/imslip:text/text() = '{1}'
				return $doc""".format(DB_NAME, name))
    xml = "x-none"
    if any(True for _ in query.iter()):
        _, xml = query.iter().next()
    query.close()
    response = xml
    return response

# gets recommendation for a user and topic
def getRecommendation(name, topic):
    cp = getContentPackage(topic)
    lip = getLearnerProfile(name)
    if cp == "x-none" or lip == "x-none": return "x-none"
    data = json.dumps({'cp': cp, 'lip': lip})
    h = {'Content-Type': 'application/xml'}
    response = requests.post(rec_sys_url+'/api/recommendation/'+name+'/' + topic, data=data, headers=h).text
    jr = json.loads(response)
    rec = jr.get("lg")
    prefs = jr.get("preferences")
    if prefs != None:
        updateLearnerPreferences(name, prefs)
    return rec

# gets cp for a topic by xquery expression
def getContentPackage(topic):
    session = createDBSession()
    session.execute("open {0}".format(DB_NAME))
    query = session.query("""
    		declare namespace imsld = "http://www.imsglobal.org/xsd/imsld_v1p0"; 
    		for $doc in collection("{0}/contentpackages")
    		    where replace(fn:base-uri($doc),'^(.*/)(.*?\.\w+$)','$2') = 'cp_{1}.xml'
    		        return $doc""".format(DB_NAME, topic))
    xml = "x-none"
    if any(True for _ in query.iter()):
        _, xml = query.iter().next()
    query.close()

    if xml == "x-none":
        return "x-none"

    query = session.query("""	
		declare namespace imscp = "http://www.imsglobal.org/xsd/imscp_v1p1";
		for $f in collection("{0}/contentpackages/cp_{1}.xml")//imscp:file/@href
			return string($f)""".format(DB_NAME, topic))
    files = []
    if any(True for _ in query.iter()):
        for _, item in query.iter():
            files.append(item)
    query.close()
    items = []
    qti = ""
    for f in files:
        query = session.query("""collection("{0}/itembank/{1}")""".format(DB_NAME, str(f)))
        if any(True for _ in query.iter()):
            _, q = query.iter().next()
            items.append(q)
            tag = f[:-4]
            qti = qti + "<qti>" + "<" + tag + ">" + q + "</" + tag + ">" + "</qti>"
        query.close()

    if qti == "x-none":
        return "x-none"

    response = "<contentpackage>" + xml + qti + "</contentpackage>"
    return response

# parses last activity from a lip of a user
def getLastActivity(name, LIP):
    tree = etree.fromstring(LIP)
    ns = {'ns': 'http://www.imsglobal.org/xsd/imslip_v1p0'}
    activities = tree.xpath("//ns:activity", namespaces=ns)
    for a in activities:
        activityType = a.xpath("ns:contentype/ns:referential/ns:indexid", namespaces=ns)[0].text
        if activityType == "last_activity":
            t = a.xpath("ns:typename/ns:tyvalue", namespaces=ns)[0].text
            topic, subtopic = t.split(": ")
            la_ref = a.xpath("ns:learningactivityref/ns:sourcedid/ns:id", namespaces=ns)[0].text
            la_state = a.xpath("ns:status/ns:date/ns:typename/ns:tyvalue", namespaces=ns)[0].text
            la_datetime = a.xpath("ns:status/ns:date/ns:datetime", namespaces=ns)[0].text
            return {
                'name': name,
                'topic': topic,
                'subtopic': subtopic,
                'ref': la_ref,
                'state': la_state,
                'datetime': la_datetime
            }
    return {
        'name': name,
        'topic': 'x-none',
        'subtopic': 'x-none',
        'ref': 'x-none',
        'state': 'x-none',
        'datetime': "x-none"
    }


# inserts cp into db
def writeContentPackage(cp, topic):
    session = createDBSession()
    session.execute("create database {0}".format(DB_NAME))
    session.add("contentpackages/cp_"+topic+".xml", cp)
    return session.info()

# inserts qti item into db
def writeItem(file, item):
    session = createDBSession()
    session.execute("open {0}".format(DB_NAME))
    session.add("itembank/" + file, item)
    return session.info()

# inserts lip into db
def writeLearnerProfile(name):
    lip = createLIP(name)
    session = createDBSession()
    session.execute("check {0}".format(DB_NAME))
    session.add("learnerprofiles/LIP_" + name + ".xml", lip)
    return session.info()

# updates last activity in lip in db by xpath and xquery
def writeActivity(name, activity):
    data = json.loads(activity)
    session = createDBSession()
    try:
        session.execute("check {0}".format(DB_NAME))
    except IOError:
        session.execute("create db {0}".format(DB_NAME))
    query = session.query("""
    			declare namespace imslip = "http://www.imsglobal.org/xsd/imslip_v1p0"; 
    			let $col := collection("{0}/learnerprofiles") 
    			for $doc in $col
    				where $doc//*[imslip:typename/imslip:tyvalue = 'First']/imslip:text/text() = '{1}'
    					return $doc""".format(DB_NAME, name))
    xml = "x-none"
    if any(True for _ in query.iter()):
        _, xml = query.iter().next()
    query.close()

    if xml == "x-none":
        return json.dumps(xml)

    tree = etree.fromstring(xml)
    ns = {'ns': 'http://www.imsglobal.org/xsd/imslip_v1p0'}
    for a in tree.xpath("//ns:activity", namespaces=ns):
        t = a.xpath("ns:contentype/ns:referential/ns:indexid", namespaces=ns)[0]
        if t.text == "last_activity":
            ref = a.xpath("ns:learningactivityref/ns:sourcedid/ns:id", namespaces=ns)[0]
            ref.text = data['ref']
            topic = a.xpath("ns:typename/ns:tyvalue", namespaces=ns)[0]
            topic.text = data['topic'] + ": " + data['subtopic']
            state = a.xpath("ns:status/ns:date/ns:typename/ns:tyvalue", namespaces=ns)[0]
            state.text = data['state']
            datetime = a.xpath("ns:status/ns:date/ns:datetime", namespaces=ns)[0]
            datetime.text = data['datetime']
    session.replace("learnerprofiles/LIP_" + name + ".xml", etree.tostring(tree))
    return session.info()

# creates lip from template
def createLIP(name):
    dataLIP = {
        'learner': {
            'id': 'LIP_' + name,
            'first_name': name,
            'last_name': 'x-none',
            'gender': 'x-none',
            'email': 'x-none',
            'preferences': [
                {'id': 'sc_easy', 'value': '0.0'},
                {'id': 'sc_medium', 'value': '0.0'},
                {'id': 'sc_difficult', 'value': '0.0'},
                {'id': 'mc_easy', 'value': '0.0'},
                {'id': 'mc_medium', 'value': '0.0'},
                {'id': 'mc_difficult', 'value': '0.0'},
                {'id': 'txt_easy', 'value': '0.0'},
                {'id': 'txt_medium', 'value': '0.0'},
                {'id': 'txt_difficult', 'value': '0.0'},
                {'id': 'order_easy', 'value': '0.0'},
                {'id': 'order_medium', 'value': '0.0'},
                {'id': 'order_difficult', 'value': '0.0'},
                {'id': 'asso_easy', 'value': '0.0'},
                {'id': 'asso_medium', 'value': '0.0'},
                {'id': 'asso_difficult', 'value': '0.0'},
                {'id': 'fact_easy', 'value': '0.0'},
                {'id': 'fact_medium', 'value': '0.0'},
                {'id': 'fact_difficult', 'value': '0.0'}
            ],
            'ts': '0',
            'activities': [
                {'topic': 'x-none', 'subtopic': 'x-none', 'ref': 'x-none', 'status': 'x-none', 'datetime': 'x-none'}
            ]
        }
    }
    loader = airspeed.CachingFileLoader("../templates")
    t = loader.load_template("template_lip.vm")
    lip = t.merge(dataLIP, loader=loader)
    return lip

# updates learner preferences in lip
def updateLearnerPreferences(name, prefs):
    xml = getLearnerProfile(name)
    tree = etree.fromstring(xml)
    ns = {'ns': 'http://www.imsglobal.org/xsd/imslip_v1p0'}
    preferences = tree.xpath("//ns:accessibility/ns:preference", namespaces=ns)
    for p in preferences:
        prefType = p.xpath("ns:contentype/ns:referential/ns:indexid", namespaces=ns)[0].text
        prefCode = p.xpath("ns:prefcode", namespaces=ns)[0]
        prefCode.text = str(prefs.get(prefType))
    ts = tree.xpath("//ns:accessibility/ns:contentype/ns:referential/ns:indexid", namespaces=ns)[0]
    ts.text = str(int(time.time()))
    session = createDBSession()
    try:
        session.execute("check {0}".format(DB_NAME))
    except IOError:
        session.execute("create db {0}".format(DB_NAME))
    session.replace("learnerprofiles/LIP_" + name + ".xml", etree.tostring(tree))
    return ""

# creates basex db session
def createDBSession():
    return BaseXClient.Session(DB_HOST, DB_PORT, DB_USER, DB_PASS)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
