import xml.sax


class MailListXMLHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.messages = []
        self.index = {}

    def startElement(self, tag, attributes):
        if tag == "index":
            self.index['page'] = attributes["page"]
            self.index['pages'] = attributes["pages"]

        elif tag == "message":
            self.messages.append({
                "linked": attributes["linked"],
                "depth": attributes["depth"],
                "id": attributes["id"]
            })
