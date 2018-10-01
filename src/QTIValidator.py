

class QTIValidator:
    def __init__(self):
        pass

    # select item specific validate method
    def validate(self, node, answer):
        if node.interaction == "sc": return self.validateSCItem(node, answer)
        if node.interaction == "mc": return self.validateMCItem(node, answer)
        if node.interaction == "asso": return self.validateASSOItem(node, answer)
        if node.interaction == "txt": return self.validateTXTItem(node, answer)
        if node.interaction == "order": return self.validateORDERItem(node, answer)

    # validate single choice item
    def validateSCItem(self, node, answer):
        print "Received Answer: " + answer

        # debug because alexa never understands my "16"
        if (answer == "sechs zehn"): answer = "sechzehn"

        isValid = False
        for a in node.answers:
            if a[1] == answer:
                if a[2] == "true":
                    isValid = True
                    pass
        return isValid

    # validate multiple choice item
    def validateMCItem(self, node, answer):
        print "Received Answer: " + answer

        # set separator of mc items
        answers = answer.split(" und ")

        valids = []
        for a in node.answers:
            if a[1] in answers:
                if a[2] == "true": valids.append(True)
                if a[2] == "false": valids.append(False)
            else:
                if a[2] == "true": valids.append(False)
                if a[2] == "false": valids.append(True)
        if False in valids:
            isValid = False
        else:
            isValid = True
        return isValid

    # validate associate item
    def validateASSOItem(self, node, answer):
        print "Received Answer: " + answer

        # set separator of asso items
        answers = answer.split(" und ")

        i = 0
        answIDS = []
        for x in answers:
            for a in node.answers:
                if a[1].lower() == x:
                    answIDS.append(a[0])
                    pass
        for a in node.answers:
            if (a[0] == answIDS[0]) and (a[2] == answIDS[1]): i = i + 1
            if (a[0] == answIDS[1]) and (a[2] == answIDS[0]): i = i + 1
            if (a[0] == answIDS[2]) and (a[2] == answIDS[3]): i = i + 1
            if (a[0] == answIDS[3]) and (a[2] == answIDS[2]): i = i + 1
        if i == len(node.answers):
            isValid = True
        else:
            isValid = False
        return isValid

    # validate text item
    def validateTXTItem(self, node, answer):
        print "Received Answer: " + answer

        isValid = False
        for a in node.answers:
            if a.lower() == answer:
                isValid = True
                pass
        return isValid

    # validate order item
    def validateORDERItem(self, node, answer):
        print "Received Answer: " + answer

        # set separators and split answer
        leer, eins = answer.split("eins")
        eins, zwei = eins.split("zwei")
        zwei, drei = zwei.split("drei")
        drei, vier = drei.split("vier")
        answs = []
        answs.append((eins, "1"))
        answs.append((zwei, "2"))
        answs.append((drei, "3"))
        answs.append((vier, "4"))

        valids = []
        for a in node.answers:
            for ao in answs:
                if a[1] == ao[0]:
                    if a[2] == ao[1]:
                        valids.append(True)
                    else:
                        valids.append(False)
                    pass
        if False in valids:
            isValid = False
        else:
            isValid = True
        return isValid