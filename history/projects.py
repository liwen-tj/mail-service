from urllib import request
import re


def getProjects():
    html = request.urlopen("https://mail-archives.apache.org/mod_mbox/").read().decode("utf-8")
    projects = re.compile(r'<h3>.+?</li><li>').findall(html)
    mail_lists = []
    for project in projects:
        name = getProjectName(project)
        lists = getProjectMails(project)
        mail_lists.append({
            "name": name,
            "mails": lists
        })
    return mail_lists


def getProjectName(proj):
    res = re.compile(r"<a name='(.*?)'>").findall(proj)
    return res[0].split(".")[0]  # delete .incubator


def getProjectMails(proj):
    res = re.compile(r"<li><a href=(.*?)</a></li>").findall(proj)
    mails = [r.split(">")[1] for r in res]
    return mails


def getHistoryMonths(proj, mail):
    base_url = "https://mail-archives.apache.org/mod_mbox/" + proj + "-" + mail + "/"
    months_html = request.urlopen(base_url).read().decode("utf-8")
    months = re.compile(r'''<span class="links" id="(.*?)">''').findall(months_html)
    return months
