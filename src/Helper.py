

# converts LG to list of dicts
def toDict(LG):
    nodesList = []
    for n in LG.nodes:
        nodesList.append(n.__dict__)
    return nodesList

# concats questions with possible answers
def buildQuestion(node):
    q = node.question
    if not (node.interaction == "txt" or node.interaction == "fact"):
        for a in node.answers:
            q = q + " " + a[1] + ", "
    return q

# debug print of LG nodes
def dprint(LG):
    for n in LG.nodes:
        print "Id: " + n.id
        print "State: " + n.state
        print "Title: " + n.title
        print "Topic: " + n.topic
        print "Subtopic: " + n.subtopic
        print "Interaction: " + n.interaction
        print "Difficulty: " + n.difficulty
        print "Question: " + n.question
        print "Answers: " + str(n.answers)
        for nx in n.next:
            print "Next: " + str(nx)
        print "-------------"
