import requests
import json


class RESTClient:

    # config RESTServer url
    url = "http://localhost:5001"

    pathes = {
        "topics": "/api/topic/titles",
        "recommendation": "/api/recommendation/<name>/<topic>",
        "learner": "/api/learner/<name>",
        "activity": "/api/learner/<name>/activity",
        "statement": "/api/lrs/statement",
        "cp": "/api/contentpackage/<topic>",
        "item": "/api/item/<fname>"
    }

    def __init__(self):
        pass

    # route get methods dep. on type
    def get(self, reqType, data=None):
        if reqType == "topics":
            return self.getTopics()
        if reqType == "recommendation":
            return self.getRecommendation(data)
        if reqType == "learner":
            return self.getLearner(data)
        if reqType == "activity":
            return self.getActivity(data)

    # route post methods dep. on type
    def post(self, reqType, data=None, payload=None):
        if reqType == "learner":
            return self.postLearner(data, payload)
        if reqType == "activity":
            return self.postActivity(data, payload)
        if reqType == "statement":
            return self.postStatement(data, payload)
        if reqType == "cp":
            return self.postContentPackage(data, payload)
        if reqType == "item":
            return self.postQtiItem(data, payload)

    # sends get topics request to REST API
    def getTopics(self):
        path = self.pathes.get('topics')
        topics = requests.get(self.url + path).text
        return json.loads(topics)

    # sends get recommendation request to REST API
    def getRecommendation(self, data):
        path = self.pathes.get('recommendation')
        path = path.replace("<name>", data.get('name'))
        path = path.replace("<topic>", data.get('topic'))
        recommendation = requests.get(self.url + path).text
        return json.loads(recommendation)

    # sends get learner request to REST API
    def getLearner(self, data):
        path = self.pathes.get('learner')
        path = path.replace("<name>", data.get('name'))
        learner = requests.get(self.url + path).text
        return json.loads(learner)

    # sends get activity request to REST API
    def getActivity(self, data):
        path = self.pathes.get('activity')
        path = path.replace("<name>", data.get('name'))
        activity = requests.get(self.url + path).text
        return json.loads(activity)

    # sends post learner request to REST API
    def postLearner(self, data, payload):
        path = self.pathes.get('learner')
        path = path.replace("<name>", data.get('name'))
        header = {'Content-Type': 'application/json'}
        response = requests.post(self.url + path, data=payload, headers=header).text
        return json.loads(response)

    # sends post activity request to REST API
    def postActivity(self, data, payload):
        path = self.pathes.get('activity')
        path = path.replace("<name>", data.get('name'))
        header = {'Content-Type': 'application/json'}
        response = requests.post(self.url + path, data=payload, headers=header).text
        return json.loads(response)

    # sends post statement request to REST API
    def postStatement(self, data, payload):
        path = self.pathes.get('statement')
        header = {'Content-Type': 'application/json'}
        response = requests.post(self.url + path, data=payload, headers=header).text
        return json.loads(response)

    # sends post contentpackage request to REST API
    def postContentPackage(self, data, payload):
        path = self.pathes.get('cp')
        path = path.replace("<topic>", data.get('topic'))
        header = {'Content-Type': 'application/xml'}
        response = requests.post(self.url + path, data=payload, headers=header).text
        return json.loads(response)

    # sends post QtiItem request to REST API
    def postQtiItem(self, data, payload):
        path = self.pathes.get('item')
        header = {'Content-Type': 'application/xml'}
        path = path.replace("<fname>", data.get('fname'))
        response = requests.post(self.url + path, data=payload, headers=header).text
        return json.loads(response)
