from lxml import etree


class XMLTools:

    schemes = {
        "cp": "../xsd/IMS_master.xsd",
        "qti": "../xsd/imsqti_v2p2.xsd"
    }

    # validate list of xml files against schemes
    def validateFiles(self, files):
        for f in files:
            xml_type = f[0]
            xml_stream = f[1]
            xsd_file = self.schemes.get(xml_type)
            if xml_type == "qti":
                continue
            isValid = self.validateStreamAgainstScheme(xml_stream, xsd_file)

            if not isValid:
                return False
        return True

    # validate xml file against xsd scheme
    def validateFileAgainstScheme(self, xml_file, xsd_file):
        doc_xml = etree.parse(xml_file)
        doc_xsd = etree.parse(xsd_file)
        xmlschema = etree.XMLSchema(doc_xsd)
        valid = xmlschema.validate(doc_xml)
        print valid
        #if not valid:
        #    print xmlschema.assertValid(doc_xml)
        return valid

    # validate xml stream against xsd scheme
    def validateStreamAgainstScheme(self, xml_stream, xsd_file):
        doc_xml = etree.fromstring(xml_stream)
        doc_xsd = etree.parse(xsd_file)
        xmlschema = etree.XMLSchema(doc_xsd)
        valid = xmlschema.validate(doc_xml)
        print valid
        #if not valid:
        #    print xmlschema.assertValid(doc_xml)
        return valid


