from urllib import request
import re
from xml import sax
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from history.xml_handler import MailListXMLHandler


class Message:
    def __init__(self, name, mail_list, month):
        self.name = name
        self.mail_list = mail_list
        self.base_url = "https://mail-archives.apache.org/mod_mbox/" + name + "-" + mail_list + "/"
        self.month = month

    def getMailData(self, mail_id, parent_id, depth):
        try:
            url = self.base_url + self.month + ".mbox/ajax/" + mail_id
            data = request.urlopen(url).read().decode("utf-8")
            mail = re.compile(r"<!\[CDATA\[(.*?)]]").findall(data)
            row = {
                "id": mail_id,
                "project": self.name,
                "maillist": self.mail_list,
                "month": self.month,
                "from": mail[0],
                "date": mail[2],
                "subject": mail[1],
                "content": mail[3],
                "depth": depth,
                "reply": parent_id
            }
            return row
        except UnicodeDecodeError or HTTPError:
            return None

    def getPageList(self, page):
        archive_url = self.base_url + self.month + ".mbox/ajax/thread?" + str(page)
        archive_xml = request.urlopen(archive_url).read().decode("utf-8")
        handler = MailListXMLHandler()
        sax.parseString(archive_xml, handler)
        return handler.messages

    def getPageData(self, messages, pool):
        pageMails = []
        original_id = ""
        for msg in messages:
            if int(msg['depth']) == 0:
                original_id = msg['id']
            if msg['linked'] == "1" and len(msg['id']) > 0:  # only store data with link
                mail = pool.submit(self.getMailData, msg['id'], original_id, msg['depth'])
                pageMails.append(mail)
        return pageMails

    def getMonthDataMultiThread(self):
        # get total page nums
        url0 = self.base_url + self.month + ".mbox/ajax/thread?0"
        xml0 = request.urlopen(url0).read().decode("utf-8")
        handler = MailListXMLHandler()
        sax.parseString(xml0, handler)
        index = handler.index
        pages = int(index['pages'])

        tp = ThreadPoolExecutor(1000)
        ms = []
        for i in range(pages):
            ms.append(tp.submit(self.getPageList, i))
        ans = []
        for m in ms:
            ans += self.getPageData(m.result(), tp)

        res = []
        for a in ans:
            try:
                tmp = a.result()
                if tmp is not None:
                    res.append(tmp)
            except BaseException as e:
                print("get data err", self.name, self.mail_list, self.month, e)
        tp.shutdown()
        return res
