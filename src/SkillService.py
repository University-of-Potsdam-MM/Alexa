import logging
import json
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
from RESTClient import RESTClient
from FiniteStateMachine import FiniteStateMachine
from SessionManager import SessionManager
from LearningGraph import LearningGraph, Node
from QTIValidator import QTIValidator
from time import strftime, localtime
import Helper

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

REST = RESTClient()
FSM = FiniteStateMachine()
SM = SessionManager()
VAL = QTIValidator()


@ask.launch
def onLaunch():
    # init FSM on launch
    session.attributes['state'] = FSM.initFSM()
    # set state launch
    session.attributes['state'] = FSM.setState("launch")
    # check if logged in
    isLoggedIn, name = SM.checkLoggedIn()
    # if logged in
    if isLoggedIn:
        session.attributes['state'] = FSM.setState("loggedin")
        # load session
        sess = SM.loadSession(name)
        # if no session exists
        if sess is None:
            # make new session and ask for topics
            session.attributes['name'] = name
            topics = REST.get("topics")
            q = render_template('ask_for_topic', topics=topics)
        # if there is a session
        else:
            # load session from db
            session.attributes = json.loads(sess["node"])
            # load current node
            jsonNode = json.loads(session.attributes['currentNode'])
            currentNode = Node()
            currentNode.loadNode(jsonNode)
            # build question
            q = Helper.buildQuestion(currentNode)
    # if not logged in
    else:
        # ask whois
        q = render_template('on_launch')
        q = q + " " + render_template('whois')
        session.attributes['last_out'] = q
    return question(q)


@ask.intent("HintIntent")
def onHintIntent():
    if session.attributes.has_key('currentNode'):
        # load node
        jsonNode = json.loads(session.attributes['currentNode'])
        currentNode = Node()
        currentNode.loadNode(jsonNode)
        # get hint
        hint = currentNode.hint
        # build question
        q = Helper.buildQuestion(currentNode)
        session.attributes['last_out'] = q
        # return hint and question
        return question(hint + " " + q)
    else:
        # if user requests hint outside of question
        s = render_template('no_question_hint')
        session.attributes['last_out'] = s
        return statement(s)


@ask.intent("YesIntent")
def onYesIntent():
    FSM.loadStateFromSession(session.attributes['state'])
    # if there is no LIP after whois or login
    if FSM.isCurrentState("whois_unknown"):
        # create new LIP for learner
        name = session.attributes['name']
        data = {'name': name}
        REST.post("learner", data=data)
        # set state newuser
        session.attributes['state'] = FSM.setState("newuser")
        # if there is a pending login - do login after LIP creation
        if session.attributes.has_key('login'):
            if session.attributes['login'] == "pending":
                onLoginIntent(name)
        # get topics
        topics = REST.get("topics")
        # confirm profile creation and ask for topic
        q = render_template('yes_profile')
        q = q + render_template('ask_for_topic', topics=topics)
        session.attributes['last_out'] = q
        return question(q)
    # if there is a LIP and learner wants to continue
    if FSM.isCurrentState("whois_known_continue"):
        # set state continue
        session.attributes['state'] = FSM.setState("continue")
        # load session
        name = session.attributes['name']
        topic = session.attributes['continue_topic']
        # get recommendation
        data = {'name': name, 'topic': topic}
        recommendation = REST.get("recommendation", data=data)
        # if topic no found
        if recommendation == "x-none":
            s = render_template('topic_not_found')
            session.attributes['last_out'] = s
            return statement(s)
        # if topic found
        else:
            # build learning graph
            LG = LearningGraph()
            LG.loadGraph(recommendation)
            # reference to last node
            last_node_ref = session.attributes['continue_node']
            # get last node
            currentNode = LG.getNode(last_node_ref)
            # save session
            session.attributes['graph'] = json.dumps(Helper.toDict(LG))
            session.attributes['currentNode'] = json.dumps(currentNode.__dict__)
            session.attributes['topic'] = topic
            SM.saveSession(session.attributes)
            # build question
            q = Helper.buildQuestion(currentNode)
            session.attributes['last_out'] = q
            return question(q)
    else:
        s = ""
        session.attributes['last_out'] = s
        return statement(s)


@ask.intent("NoIntent")
def onNoIntent():
    FSM.loadStateFromSession(session.attributes['state'])
    # if learner rejects profile creation
    if FSM.isCurrentState("whois_unknown"):
        # set state noprofile
        session.attributes['state'] = FSM.setState("noprofile")
        # finishing statement
        s = render_template('no_profile')
        session.attributes['last_out'] = s
        return statement(s)
    # if learner rejects continuing topic
    if FSM.isCurrentState("whois_known_continue"):
        # set state not_continue
        session.attributes['state'] = FSM.setState("not_continue")
        # get topics and ask for one of them
        topics = REST.get("topics")
        q = render_template('ask_for_topic', topics=topics)
        session.attributes['last_out'] = q
        return question(q)
    else:
        return statement("")


@ask.intent("LoginIntent")
def onLoginIntent(name):
    # get LIP of learner
    data = {'name': name}
    LIP = REST.get("activity", data=data)
    # if there is no LIP
    if LIP == "x-none":
        # set state whois_unknown
        session.attributes['state'] = FSM.setState("whois_unknown")
        # save to indicate login after LIP creation
        session.attributes['login'] = "pending"
        session.attributes['name'] = name
        # ask for creation and login
        q = render_template('user_unknown', name=name)
        session.attributes['last_out'] = q
        return question(q)
    # if there is a LIP
    else:
        # do login
        SM.login(name)
        # statement finish login - restart for learning
        s = render_template('user_loggedin', name=name)
        session.attributes['last_out'] = s
        return statement(s)


@ask.intent("LogoutIntent")
def onLogoutIntent():
    # do and confirm logout
    SM.logout()
    s = "Du wurdest ausgeloggt."
    session.attributes['last_out'] = s
    return statement(s)


@ask.intent("WhoisIntent")
def onWhoisIntent(name):
    # set state whois
    session.attributes['state'] = FSM.setState("whois")
    name = name.lower()
    session.attributes['name'] = name
    # get LIP of learner
    data = {'name': name}
    LIP = REST.get("activity", data=data)
    # if there is no LIP
    if LIP == "x-none":
        # unknown user - ask to create new user
        session.attributes['state'] = FSM.setState("whois_unknown")
        q = render_template('newuser', name=name)
    # if there is a LIP
    else:
        # known user - check for last activity
        session.attributes['state'] = FSM.setState("whois_known")
        last_activity = dict(LIP)
        # if there is no last activity
        if last_activity["topic"] == "x-none":
            # known user - no last activity - set state fresh
            session.attributes['state'] = FSM.setState("whois_known_fresh")
            # get topics and ask for choosing one of them
            topics = REST.get("topics")
            q = render_template('welcome_back', name=name)
            q = q + render_template('ask_for_topic', topics=topics)
        # if there is a last activity
        else:
            # known user - with last activity - set state continue
            session.attributes['state'] = FSM.setState("whois_known_continue")
            # load node for continuing
            session.attributes['continue_topic'] = last_activity["topic"]
            session.attributes['continue_node'] = last_activity["ref"]
            # ask for continuing topic
            q = render_template('welcome_back', name=name)
            q = q + " " + render_template('ask_for_continue', topic=last_activity["topic"])
    session.attributes['last_out'] = q
    return question(q)


@ask.intent("RecommendationIntent")
def onRecommendationIntent(topic):
    # set state recommendation
    session.attributes['state'] = FSM.setState("recommendation")
    # get recommendation
    name = session.attributes['name']
    topic = topic.lower()
    data = {'name': name, 'topic': topic}
    recommendation = REST.get("recommendation", data=data)
    # if topic not found
    if recommendation == "x-none":
        s = "Thema nicht gefunden"
        session.attributes['last_out'] = s
        return statement(s)
    # if topic found
    else:
        # build learning graph
        LG = LearningGraph()
        LG.loadGraph(recommendation)
        # get first node
        node = LG.getStartNode()
        # save session
        session.attributes['graph'] = json.dumps(Helper.toDict(LG))
        session.attributes['currentNode'] = json.dumps(node.__dict__)
        session.attributes['topic'] = json.dumps(topic)
        SM.saveSession(session.attributes)
        # build question
        q = Helper.buildQuestion(node)
        session.attributes['last_out'] = q
        return question(q)


@ask.intent("AnswerIntent")
def onAnswerIntent(answer):
    # set state answer
    session.attributes['state'] = FSM.setState("answer")
    # load LG
    jsonLG = json.loads(session.attributes['graph'])
    LG = LearningGraph()
    LG.loadGraph(jsonLG)
    # load currentNode
    jsonNode = json.loads(session.attributes['currentNode'])
    currentNode = Node()
    currentNode.loadNode(jsonNode)
    name = session.attributes['name']
    # validate answer, fact always true
    if currentNode.interaction == "fact":
        isValid = True
    else:
        # validate qti item
        isValid = VAL.validate(currentNode, answer.lower())

    payload = {
        'name': name,
        'verb': "experienced",
        'activity': "resource",
        'activityid': currentNode.id,
        'difficulty': currentNode.difficulty,
        'interaction': currentNode.interaction,
        'topic': currentNode.topic,
        'subtopic': currentNode.subtopic,
        'score': 1 if isValid else 0,
        'success': isValid
    }

    # sends statement to LRS
    REST.post("statement", data=None, payload=json.dumps(payload))

    # get next node of LG
    nextNode = LG.getNextNode(currentNode, isValid)
    if nextNode:
        session.attributes['currentNode'] = json.dumps(nextNode.__dict__)
        # save session
        SM.saveSession(session.attributes)

        payload = {
            'topic': nextNode.topic,
            'subtopic': nextNode.subtopic,
            'ref': nextNode.id,
            'state': nextNode.state,
            'datetime': strftime("%d.%m.%Y %H:%M:%S", localtime())
        }

        # save reached activity
        REST.post("activity", data={'name': name}, payload=json.dumps(payload))
        q = Helper.buildQuestion(nextNode)
        # if last answer was valid
        if isValid:
            # give positive feedback and ask next question
            qq = currentNode.feedback_pos + " " + q
            session.attributes['last_out'] = q
            return question(qq)
        else:
            # give negative feedback and ask next question
            qq = currentNode.feedback_neg + " " + q
            session.attributes['last_out'] = q
            return question(qq)
    else:
        # del session
        SM.delSession(name)
        s = render_template('fin_topic')
        session.attributes['last_out'] = s
        return statement(s)


@ask.intent("ContinueIntent")
def onContinueIntent():
    if session.attributes.has_key('currentNode'):

        # load current node
        jsonNode = json.loads(session.attributes['currentNode'])
        currentNode = Node()
        currentNode.loadNode(jsonNode)

        name = session.attributes['name']

        if currentNode.interaction == "fact":
            payload = {
                'name': name,
                'verb': "experienced",
                'activity': "resource",
                'activityid': currentNode.id,
                'difficulty': currentNode.difficulty,
                'interaction': currentNode.interaction,
                'topic': currentNode.topic,
                'subtopic': currentNode.subtopic,
                'score': 1 if True else 0,
                'success': True
            }

            # sends statement to LRS
            REST.post("statement", data=None, payload=json.dumps(payload))  ###

        # load LG and get next node
        jsonLG = json.loads(session.attributes['graph'])
        LG = LearningGraph()
        LG.loadGraph(jsonLG)
        nextNode = LG.getNextNode(currentNode, True)

        if nextNode:
            session.attributes['currentNode'] = json.dumps(nextNode.__dict__)
            SM.saveSession(session.attributes)

            payload = {
                'topic': nextNode.topic,
                'subtopic': nextNode.subtopic,
                'ref': nextNode.id,
                'state': nextNode.state,
                'datetime': strftime("%d.%m.%Y %H:%M:%S", localtime())
            }
            # update last activity
            REST.post("activity", data={'name': name}, payload=json.dumps(payload))
            # build next question
            q = Helper.buildQuestion(nextNode)
            session.attributes['last_out'] = q
            return question(q)
        else:
            # del session
            SM.delSession(name)
            s = render_template('fin_topic')
            session.attributes['last_out'] = s
            return statement(s)


@ask.intent("AMAZON.StopIntent")
def onStopIntent():
    s = render_template('on_stop')
    return statement(s)


@ask.intent("AMAZON.CancelIntent")
def onCancelIntent():
    s = render_template('on_cancel')
    return statement(s)


@ask.intent("AMAZON.HelpIntent")
def onHelpIntent():
    FSM.loadStateFromSession(session.attributes['state'])
    # help messages depending on states
    if FSM.isCurrentState("start"): s = ""
    if FSM.isCurrentState("launch"): s = render_template('help_name')
    if FSM.isCurrentState("loggedin"): s = ""
    if FSM.isCurrentState("whois"): s = ""
    if FSM.isCurrentState("whois_unknown"): s = render_template('help_new_profile')
    if FSM.isCurrentState("whois_known"): s = ""
    if FSM.isCurrentState("whois_known_fresh"): s = render_template('help_topic')
    if FSM.isCurrentState("whois_known_continue"): s = render_template('help_answer')
    if FSM.isCurrentState("newuser"): s = render_template('help_topic')
    if FSM.isCurrentState("noprofile"): s = ""
    if FSM.isCurrentState("continue"): s = render_template('answer')
    if FSM.isCurrentState("not_continue"): s = render_template('help_topic')
    if FSM.isCurrentState("recommendation"): s = render_template('help_answer')
    if FSM.isCurrentState("answer"): s = render_template('help_answer')
    return question(s)

@ask.intent("RepeatIntent")
def onRepeatIntent():
    q = session.attributes['last_out']
    return question(q)


if __name__ == '__main__':
    app.run(debug=True)
