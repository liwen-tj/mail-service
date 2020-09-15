from datetime import datetime
from db import insertMonthMessage
from history.projects import getProjects


def update_message():
    yy_ = datetime.now().year
    mm_ = datetime.now().month
    cur_month = str(yy_) + ("0" + str(mm_) if mm_ < 10 else str(mm_))
    projects = getProjects()
    for p in projects:
        try:
            if p['name'] == 'asf-wide':
                continue
            mails = p['mails']
            for m in mails:
                insertMonthMessage(p['name'], m, cur_month)
        except:
            pass


if __name__ == '__main__':
    update_message()
