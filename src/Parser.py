from lxml import etree
from LearningGraph import LearningGraph, Node


class Parser:
    # parse ims cp
    def parseCP(self, CP):
        graph = LearningGraph()
        edges = []
        # clean and parse xml to elementtree
        tree = self.clean(etree.fromstring(CP))
        i = 0
        # parse nodes
        for la in tree.xpath("//learning-design/components/activities/learning-activity"):
            node = Node()
            node.id = la.attrib['identifier']
            if i == 0:
                node.state = "start"
            i += 1
            node.title = la.xpath('title')[0].text
            for itm in la.xpath('prerequisites/item'):
                # optional if you need preqs
                #edges.append((itm.attrib['identifierref'], la.attrib['identifier'], "none", "none", "pre"))
                pass
            env_ref = la.xpath('environment-ref')[0].attrib['ref']
            node.feedback_pos = la.xpath('on-completion/feedback-description/item/title')[0].text
            node.feedback_neg = la.xpath('on-completion/feedback-description/item/title')[1].text
            node.hint = la.xpath('activity-description/item/title')[0].text
            env = la.xpath("//environments/environment[@identifier='" + env_ref + "']")
            res_id = env[0].xpath('learning-object/item')[0].attrib['identifierref']
            file = tree.xpath("//resource[@identifier='" + res_id + "']/file")[0].attrib['href']
            node.difficulty = env[0].xpath('learning-object/metadata/lom/educational/difficulty/value/langstring')[
                0].text
            for keyword in env[0].xpath('learning-object/metadata/lom/general/keyword/langstring'):
                key, word = keyword.text.split(":")
                if (key == "interaction"): node.interaction = word
                if (key == "topic"): node.topic = word
                if (key == "subtopic"): node.subtopic = word

            tag = file[:-4]
            node.question = tree.xpath("//qti/" + tag + "//prompt")[0].text
            if (node.interaction == "sc"):
                for answ in tree.xpath("//qti/" + tag + "//simpleChoice"):
                    aid = answ.attrib['identifier']
                    atxt = answ.text
                    acor = "false"
                    if (aid == tree.xpath("//qti/" + tag + "//correctResponse/value")[0].text):
                        acor = "true"
                    node.answers.append((aid, atxt, acor))
            if (node.interaction == "mc"):
                for answ in tree.xpath("//qti/" + tag + "//simpleChoice"):
                    aid = answ.attrib['identifier']
                    atxt = answ.text
                    acor = "false"
                    for cr in tree.xpath("//qti/" + tag + "//correctResponse/value"):
                        if (aid == cr.text):
                            acor = "true"
                    node.answers.append((aid, atxt, acor))
            if (node.interaction == "txt"):
                for cr in tree.xpath("//qti/" + tag + "//correctResponse/value"):
                    node.answers.append(cr.text)
            if (node.interaction == "asso"):
                for answ in tree.xpath("//qti/" + tag + "//simpleAssociableChoice"):
                    aid = answ.attrib['identifier']
                    atxt = answ.text
                    for cr in tree.xpath("//qti/" + tag + "//correctResponse/value"):
                        a1, a2 = cr.text.split(" ")
                        if (a1 == aid):
                            aasso = a2
                        if (a2 == aid):
                            aasso = a1
                    node.answers.append((aid, atxt, aasso))
            if (node.interaction == "order"):
                for answ in tree.xpath("//qti/" + tag + "//simpleChoice"):
                    aid = answ.attrib['identifier']
                    atxt = answ.text
                    acor = "false"
                    i = 0
                    for cr in tree.xpath("//qti/" + tag + "//correctResponse/value"):
                        i = i + 1
                        if (aid == cr.text):
                            arank = str(i)
                    node.answers.append((aid, atxt, arank))
            graph.nodes.append(node)

        # parse edges
        conditions = tree.xpath("//conditions")[0]
        conditions_x = conditions.xpath("./if")
        conditions_y = conditions.xpath("./then")
        len_c = len(conditions_x)
        for i in range(0,len_c):
            currentNodeId = conditions_x[i].xpath("./and/is/property-value")[1].text
            p_succeed = conditions_x[i].xpath("./and/is/property-value")[2].text
            p_rec_interaction = conditions_x[i].xpath("./and/is/property-value")[3].text
            p_rec_difficulty = conditions_x[i].xpath("./and/is/property-value")[4].text
            targetNodeId = conditions_y[i].xpath("./show/learning-activity-ref")[0].attrib['ref']
            edge = (currentNodeId, targetNodeId, p_rec_interaction, p_rec_difficulty, p_succeed)
            edges.append(edge)

        # add edges to specific nodes adj.list
        for n in graph.nodes:
            for e in edges:
                if (e[0] == n.id):
                    n.next.append((e[1], e[2], e[3], e[4], 0.0))
        self.dprint(graph)
        return graph

    # cleans etree of ns uris
    def clean(self, tree):
        # xpath query for selecting all element nodes in namespace
        query = "descendant-or-self::*[namespace-uri()!='']"
        # for each element returned by the above xpath query...
        for element in tree.xpath(query):
            # replace element name with it's local name
            element.tag = etree.QName(element).localname
        return tree

    # parse LIP for preferences
    def parseLIP(self, LIP):
        tree = etree.fromstring(LIP)
        ns = {'ns': 'http://www.imsglobal.org/xsd/imslip_v1p0'}
        ts = tree.xpath("//ns:accessibility/ns:contentype/ns:referential/ns:indexid", namespaces=ns)[0].text
        preferences = tree.xpath("//ns:accessibility/ns:preference", namespaces=ns)
        prefList = []
        for p in preferences:
            prefType = p.xpath("ns:contentype/ns:referential/ns:indexid", namespaces=ns)[0].text
            prefCode = p.xpath("ns:prefcode", namespaces=ns)[0].text
            prefList.append( (prefType, prefCode) )
        return prefList, ts

    # debug print LG
    def dprint(self, graph):
        for n in graph.nodes:
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
            print "#####"
