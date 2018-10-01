from LRSClient import LRSClient
from operator import itemgetter
from flask import Flask, request
from Parser import Parser
import json
import time


app = Flask(__name__)

#upd_intervall = 7 * 24 * 60 * 60 # weekly
#upd_intervall = 1 * 24 * 60 * 60 # dayly
upd_intervall = 0 * 24 * 60 * 60  # always

@app.route('/api/recommendation/<name>/<topic>', methods=('GET', 'POST'))
def apiRecommendation(name, topic):
    if request.method == 'POST':

        # load CP and LIP
        data = json.loads(request.data)
        cp = data.get("cp")
        lip = data.get("lip")

        # parse CP and LIP
        parser = Parser()
        lg = parser.parseCP(cp)
        preferences, ts = parser.parseLIP(lip)

        # check last preference update
        time_diff = int(time.time()) - int(ts)

        # if its outdated, update preferences
        if time_diff > upd_intervall:
            ranked_results = analyze(name)
            update = True
        # if its timely, load preferences
        else:
            ranked_results = preferences
            update = False

        # recommend nodes in LG
        lg.updateNodeRecommendations(dict(ranked_results))

        # send LG alone or LG with preferences as response
        a = toDict(lg)
        if update:
            b = dict(ranked_results)
        else:
            b = None
        r = {'lg': a, 'preferences': b}
        response = json.dumps(r)
        return response

# change weights if needed
weights = {
    "sc_easy": 1.0,
    "sc_medium": 1.5,
    "sc_difficult": 2.0,
    "mc_easy": 1.5,
    "mc_medium": 2.0,
    "mc_difficult": 2.5,
    "txt_easy": 1.5,
    "txt_medium": 2.0,
    "txt_difficult": 2.5,
    "order_easy": 1.5,
    "order_medium": 2.0,
    "order_difficult": 2.5,
    "asso_easy": 2.0,
    "asso_medium": 2.5,
    "asso_difficult": 3.0,
    "fact_easy": 4.0,
    "fact_medium": 4.5,
    "fact_difficult": 5.0
}

def analyze(name):

    # get Learning Records
    lrs = LRSClient()
    statements = lrs.getStatements(name)

    # count different statements
    counts, total = count(statements)

    results = []

    # for every preftype update prefvalue
    for key, val in counts.iteritems():
        # get count of succ and fail statements
        succ = val[0]
        fail = val[1]

        # total count of statements
        total_sf = succ + fail

        # if there are statements of the current preftype
        if total_sf != 0:
            # calc scaled amount between 0 and 1 (sum is 1)
            succ_scale = succ*(100.0/total_sf)/100.0
            fail_scale = fail*(100.0/total_sf)/100.0
        # if there are no statements - set nearly same amount
        else:
            succ_scale = 0.6
            fail_scale = 0.4

        # get difference: > 0 is more succ and < 0 is more fail
        diff = succ_scale - fail_scale

        # weight value dependent of preftype
        diff_weighted = diff * weights.get(key)

        # balance preftype amount
        stake = total - total_sf
        stake_scale = stake/100.0
        result = diff_weighted * stake_scale

        result = float("{0:.2f}".format(result))

        # add preference to results list
        results.append( (key,result) )

    # sort results list as ranked list
    ranked_results = sorted(results,key=itemgetter(1), reverse=True)
    return ranked_results

def count(statements):

    # total amount statements
    total = len(statements.content.statements)

    # preftype with tuple of (#succ,#fail)
    counts = {
        "sc_easy": (0, 0),
        "sc_medium": (0, 0),
        "sc_difficult": (0, 0),
        "mc_easy": (0, 0),
        "mc_medium": (0, 0),
        "mc_difficult": (0, 0),
        "txt_easy": (0, 0),
        "txt_medium": (0, 0),
        "txt_difficult": (0, 0),
        "order_easy": (0, 0),
        "order_medium": (0, 0),
        "order_difficult": (0, 0),
        "asso_easy": (0, 0),
        "asso_medium": (0, 0),
        "asso_difficult": (0, 0),
        "fact_easy": (0, 0),
        "fact_medium": (0, 0),
        "fact_difficult": (0, 0)
    }

    k1 = "http://id.tincanapi.com/extension/interaction"
    k2 = "http://id.tincanapi.com/extension/difficulty"

    # iterate statements
    for s in statements.content.statements:
        # build preftype
        if s.context.extensions.has_key(k1) and s.context.extensions.has_key(k2):
            i = s.context.extensions[k1]
            d = s.context.extensions[k2]
            x = i + "_" + d

            # if statement has successful result increment first tuple value
            if s.result.success:
                counts[x] = (counts.get(x)[0] + 1, counts.get(x)[1])
            # if statement has fail result increment second tuple value
            else:
                counts[x] = (counts.get(x)[0], counts.get(x)[1] + 1)

    return counts, total

# converts LG to dict
def toDict(LG):
    lon = []
    for n in LG.nodes:
        lon.append(n.__dict__)
    return lon


if __name__ == '__main__':
    app.run(debug=True, port=5002)
