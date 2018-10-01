from operator import itemgetter

# LG class
class LearningGraph:

    nodes = []

    def __init__(self):
        self.nodes = []

    # returns node by id
    def getNode(self, id):
        for node in self.nodes:
            if node.id == id:
                return node
        return None

    # returns start node
    def getStartNode(self):
        for node in self.nodes:
            if node.state == "start":
                return node
        return None

    # returns next node depending of recommendation
    def getNextNode(self, cnode, isValid):
        # sort for rec value
        sono = sorted(cnode.next, key=itemgetter(4), reverse=True)
        # return recommended node which is reachable
        for n in sono:
            if isValid:
                if n[3] == "true":
                    return self.getNode(n[0])
            else:
                if n[3] == "false":
                    return self.getNode(n[0])
        return None

    # load graph from session, converts list of dicts to nodes list = LG
    def loadGraph(self, data):
        for n in data:
            node = Node()
            node.loadNode(n)
            self.nodes.append(node)
        return

    # update rec values of nodes if there are new preferences updates
    def updateNodeRecommendations(self, prefs):
        for node in self.nodes:
            index = -1
            for nx in node.next:
                index = index+1
                if nx[1] != "none" and nx[2] != "none":
                    i = nx[1] + "_" + nx[2]
                    a = prefs.get(i)
                    node.next[index] = (nx[0], nx[1], nx[2], nx[3], a)

# node class
class Node:

    # node fields
    id = ""
    state = ""
    title = ""
    topic = ""
    subtopic = ""
    interaction = ""
    difficulty = ""
    question = ""
    answers = []
    feedback_pos = ""
    feedback_neg = ""
    hint = ""
    next = []

    # init node
    def __init__(self):
        self.id = ""
        self.state = ""
        self.title = ""
        self.topic = ""
        self.subtopic = ""
        self.interaction = ""
        self.difficulty = ""
        self.question = ""
        self.answers = []
        self.feedback_pos = ""
        self.feedback_neg = ""
        self.hint = ""
        self.next = []

    # load node from dict (from session)
    def loadNode(self, n):
        self.id = n["id"]
        self.state = n["state"]
        self.title = n["title"]
        self.topic = n["topic"]
        self.subtopic = n["subtopic"]
        self.interaction = n["interaction"]
        self.difficulty = n["difficulty"]
        self.feedback_pos = n["feedback_pos"]
        self.feedback_neg = n["feedback_neg"]
        self.hint = n["hint"]
        self.question = n["question"]
        for a in n["answers"]:
            self.answers.append(a)
        for nx in n["next"]:
            self.next.append((nx[0], nx[1], nx[2], nx[3], nx[4]))
        return
