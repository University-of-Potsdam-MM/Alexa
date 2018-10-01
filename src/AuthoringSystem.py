import airspeed
import yaml
from RESTClient import RESTClient
from XMLTools import XMLTools


class AuthoringSystem:

    templates = {
        "path": "../templates",
        "cp": "template_cp.vm",
        "sc": "template_sc.vm",
        "mc": "template_mc.vm",
        "txt": "template_txt.vm",
        "order": "template_order.vm",
        "asso": "template_asso.vm",
        "fact": "template_fact.vm",
    }

    def insertResources(self):
        # read learning content from json
        with open('../content/cp.json') as f:
           res = yaml.safe_load(f.read())
        # load ims cp template and merge content into cp
        loader = airspeed.CachingFileLoader(self.templates.get("path"))
        t = loader.load_template(self.templates.get("cp"))
        cp = t.merge(res, loader=loader)

        # validate ims cp (incl. ld, md)
        xmltools = XMLTools()
        scheme_path = "../xsd/IMS_master.xsd"
        xmltools.validateStreamAgainstScheme(cp, scheme_path)

        # get topic name for filename
        topic = res.get("learning_design").get("title").lower()

        # write cp file to local file
        with open('../xml/cp_'+topic+'.xml', 'w+') as f:
            f.write(cp)

        # write cp file to db
        REST = RESTClient()
        r = REST.post("cp", data={'topic': topic}, payload=cp)
        print r

        # build and write qti items to db
        for la in res['learning_activities']:
            # load qti template
            t = loader.load_template(self.templates.get(la['content']['interaction']))
            qti = t.merge(la, loader=loader)

            # write qti files to local files
            fname = 'qti_' + la['id'] + '.xml'
            with open('../xml/' + fname, 'w+') as f:
                f.write(qti)

            # write qti files to db
            r = REST.post("item", data={'fname': fname}, payload=qti)
            print r


if __name__ == '__main__':
    a = AuthoringSystem()
    a.insertResources()
