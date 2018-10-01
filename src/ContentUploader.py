import zipfile, sys
from RESTClient import RESTClient
from XMLTools import XMLTools
from lxml import etree


class ContentUploader:
    # extract valid files from zip
    def extractZipFiles(self, zip_file):
        files = []
        with zipfile.ZipFile(zip_file) as z:
            for file in z.namelist():
                # get cp manifest
                if file == "imsmanifest.xml":
                    with z.open(file) as f:
                        manifest = f.read()
                        files.append(("cp", manifest))
                # get qti items
                if file.startswith('qti/') and file.endswith('.xml'):
                    with z.open(file) as f:
                        qti = f.read()
                        files.append(("qti", qti))
        return files


    def upload(self, filepath):
        # extract zip
        files = self.extractZipFiles(filepath)
        # validate files
        xmltools = XMLTools()
        allValid = xmltools.validateFiles(files)
        if len(files) != 0 and allValid:
            REST = RESTClient()
            for filetype, content in files:
                if filetype == "cp":
                    cp = content

                    # get topic name for filename
                    tree = etree.fromstring(cp)
                    ns = {'ns': 'http://www.imsglobal.org/xsd/imsld_v1p0'}
                    topic = tree.xpath('//ns:learning-design/ns:title', namespaces=ns)[0].text

                    # write cp file to db
                    r = REST.post("cp", data={'topic': topic}, payload=cp)
                    print r

                if filetype == "qti":
                    qti = content

                    # get item id for filename
                    tree = etree.fromstring(qti)
                    id = tree.xpath("/*[local-name()]")[0].attrib['identifier']
                    id = id.split("ITM_")[1]
                    fname = 'qti_' + id + '.xml'

                    #write qti file to db
                    r = REST.post("item", data={'fname': fname}, payload=qti)
                    print r


if __name__ == "__main__":
    # check args
    if len(sys.argv) == 3:
        # if zip file is specified
        if sys.argv[1] == "-zip":
            filename = sys.argv[2]
            c = ContentUploader()
            c.upload("../zip/" + filename)
        else:
            print "usage: ContentUploader.py -zip <yourfile>"
    else:
        print "usage: ContentUploader.py -zip <yourfile>"

