import pymongo
from history.projects import getProjects, getHistoryMonths
from history.messages import Message
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count
import os

env = dict(os.environ)

MONGO_ADDRESS = 'mongodb://58.198.176.9:30270/' if not env.__contains__('MONGO_ADDRESS') else env['MONGO_ADDRESS']
MONGO_MAILS_USER_NAME = 'liwen' if not env.__contains__('MONGO_MAILS_USER_NAME') else env['MONGO_MAILS_USER_NAME']
MONGO_MAILS_USER_PASSWORD = env['MONGO_MAILS_USER_PASSWORD']
MONGO_MAILS_MECHANISM = 'SCRAM-SHA-1' if not env.__contains__('MONGO_MAILS_MECHANISM') else env['MONGO_MAILS_MECHANISM']

client = pymongo.MongoClient(MONGO_ADDRESS)
client.mails.authenticate(MONGO_MAILS_USER_NAME, MONGO_MAILS_USER_PASSWORD, mechanism=MONGO_MAILS_MECHANISM)
# client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")

mails_db = client["mails"]
col = mails_db.list_collection_names()
ml = mails_db['maillist']
ms = mails_db['message']
dl = mails_db['downloaded']
og = mails_db['original']
yy_ = datetime.now().year
mm_ = datetime.now().month
cur_month = str(yy_) + ("0" + str(mm_) if mm_ < 10 else str(mm_))


def createIndex():
    ml.drop()
    ml.create_index([('name', 1)], unique=True, background=True)
    ms.drop()
    ms.create_index([('id', 1)], unique=True, background=True)
    dl.drop()
    dl.create_index([('project', 1), ('maillist', 1), ('month', 1)], unique=True, background=True)


def ogCreateIndex():
    og.drop()
    og.create_index([('project', 1), ('maillist', 1), ('month', 1)], unique=True, background=True)


def insertMailLists():
    try:
        data = getProjects()
        ml.insert_many(data)
        return data
    except BaseException as e:
        print("err: ", e)


def upsertDownloader(proj, mail, mon, n):
    cond = {
        "project": proj,
        "maillist": mail,
        "month": mon
    }
    mss = dl.find_one(cond)
    if mss is None:
        cond["num"] = n
        dl.insert_one(cond)
    else:
        update_num = {"$set": {"num": n}}
        dl.update_one(cond, update_num)


def insertMonthMessage(proj, mail, mon):
    # 历史月份可能不需要再导入了
    if mon != cur_month:
        cond = {
            "project": proj,
            "maillist": mail,
            "month": mon
        }
        mss = dl.find_one(cond)
        oss = og.find_one(cond)
        if mss is not None and oss['num'] - mss['num'] < 5:
            print(proj, mon, "already okay")
            return

    # 导入该月的数据
    try:
        start = time.time()
        pro = Message(proj, mail, mon)
        month_res = pro.getMonthDataMultiThread()
        if mon == cur_month:
            for mr in month_res:
                try:
                    ms.insert_one(mr)
                except:
                    pass
        else:
            ms.insert_many(month_res)
        upsertDownloader(proj, mail, mon, len(month_res))
        print(proj, mon, len(month_res), "month okay")
    except BaseException as e:
        print("get month data err: ", proj, mail, mon, e)


def getMailLists():
    mss = ml.find({}, {"_id": 0, "name": 1, "mails": 1})
    return [k for k in mss]


def getOneMailList(project):
    mss = mails_db['maillist'].find({'name': project})
    for t in mss:
        return t['mails']


def getDownloaded(project, maillist=None):
    cond = {'project': project}
    if maillist is not None:
        cond['maillist'] = maillist
    mss = dl.find(cond)
    data = []
    for _m in mss:
        del _m['_id']
        data.append(_m)
    return data


def getMessages(cond):
    res = ms.find(cond)
    data = []
    for r in res:
        del r['_id']
        data.append(r)
    return data


def insertMsgCount(proj, mail, month, msg):
    try:
        bad = (len(month) != len(msg))
        data = []
        for i in range(len(month)):
            data.append({
                'project': proj,
                'maillist': mail,
                'month': month[i],
                'msg': -1 if bad else msg[i]
            })
        og.insert_many(data)
        print("insert original okay: ", proj, mail)
    except BaseException as e:
        print("insert original err: ", proj, mail)


def init():
    ogCreateIndex()
    projects = getProjects()
    print("Get projects done...")
    pp = Pool(cpu_count())
    for p in projects:
        if p['name'] == 'asf-wide':
            continue
        mails = p['mails']
        for m in mails:
            try:
                months, msg_count = getHistoryMonths(p['name'], m)
                insertMsgCount(p['name'], m, months, msg_count)
            except BaseException as e:
                print("get history month err: ", p['name'], m, e)
                continue
            try:
                for mon in months:
                    pp.apply_async(insertMonthMessage, args=(p['name'], m, mon))
            except BaseException as e:
                print("insert month msg err: ", p['name'], m, e)
    print("Hooray!! All data add done..")
    pp.close()
    pp.join()


if __name__ == '__main__':
    init()
