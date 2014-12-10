#!/usr/bin/python -u
# -*- coding: UTF-8 -*-

import pymongo
import datetime
import calendar
import smtplib
import quopri
import base64

import sys
reload(sys)
sys.setdefaultencoding('utf8')

if sys.stdout.encoding is None:
    import codecs
    writer = codecs.getwriter("utf-8")
    sys.stdout = writer(sys.stdout)

comment='''

        cnt:新增注册用户数
        scnt:新增代运营用户数
        zcnt_all:累计注册用户数
        zcnt_all_D:累计注册代运营用户数
        acnt2:有发车操作的用户数
        acnt:有发车操作的用户中的新增用户数
        xcnt:有发车操作的用户中的代运营用户数
        sscnt:新增代运营用户有发车的用户
        acnt2_number:总发车数量
        wcnt:当日累计车源总量
        rcnt:当日在售车源总量
        ant_number:新增用户发车数量
        xcnt_number:代运营用户发车数量
        scnt_number:新增代运营用户发车数量


'''

def send_mail(content,daily_flag):
    daily_flag=daily_flag+"-日统计"
    daily_flag=base64.encodestring(daily_flag).split('\n')[0]
    smtp = smtplib.SMTP()   
    smtp.connect("smtp.exmail.qq.com", "25")   
    smtp.login('junwei.zhuang@kanche.com', 'zhuangjunwei12')   
    smtp.sendmail('junwei.zhuang@kanche.com', 'dennis.zhao@kanche.com',
        'From: junwei.zhuang@kanche.com\r\n' + 
        'To: dennis.zhao@kanche.com\r\n' +
        'Content-Type: text/plain; charset=UTF-8\r\n' + 
        'Content-Transfer-Encoding: quoted-printable\r\n' +
        'Subject: =?UTF-8?B?'+daily_flag+'?=\r\n\r\n' +
        quopri.encodestring(content))   
    smtp.quit() 

def statistics_daily(week, ul,daily_flag):
    conn = pymongo.Connection('127.0.0.1', tz_aware=True)
    db = conn['kanche']
    user_col = db['user']
    vehicle_col = db['vehicle']
    substitute_user_col = db['substitute_user']
    start = daily[0]
    stop = daily[1]

    cnt=0  #当日新增注册用户数



    scnt = 0 #每日新增的代运营用户
    scnt_number=0 #新增代运营用户发车数量
    sscnt=0
    acnt = 0    #2 每日新增的用户中发车的用户s
    ant_number=0  #每日新增用户发车量
    all_users = user_col.find({"$and": [{"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}, {"mobile": {"$nin": ul}}]})
    for user in all_users:
        cnt += 1
        substitute_user = substitute_user_col.find_one({"user_id": user["_id"]})
        if substitute_user is not None and substitute_user["enable"] is True:
            scnt += 1
            vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
            if vcnt>0:
                scnt_number+=vcnt
                sscnt+=1
        vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
        if vcnt > 0:
            acnt += 1
            ant_number+=vcnt

    acnt2 = 0   #1  本日有发车操作的用户数
    acnt2_number=0   #当日总发车数量
    all_users = user_col.find({"mobile":{"$nin":ul}})
    all_user=[]
    for i in all_users:
        all_user.append(i)
    for user in all_user:
        vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
        if vcnt > 0:
            acnt2 += 1
            acnt2_number+=vcnt
    xcnt=0	     #3  本日内有发车操作的用户中的代运营用户数
    xcnt_number=0
    for user in all_user:
        substitute_user = substitute_user_col.find_one({"user_id": user["_id"]})
        if substitute_user is not None and substitute_user["enable"] is True:
            vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
            if vcnt>0:
                xcnt+=1
                xcnt_number+=vcnt



    zcnt_all=0 #累计注册用户数
    wcnt=0   #当日累计车源总量
    rcnt=0
    all_users_ALL = user_col.find({"$and": [ {"create_at": {"$lt": stop}}, {"mobile": {"$nin": ul}}]})
    all_user_ALL=[]
    for i in all_users_ALL:
        all_user_ALL.append(i)
    for user in all_user_ALL:

        zcnt_all+=1
        vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$lt": stop}}]}).count()
        wcnt+=vcnt
        vcnt= vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$lt": stop}},{"status.offline":False}]}).count()
        rcnt+=vcnt
    zcnt_all_D=0 #累计注册代运营用户数

    for user in all_user_ALL:
        substitute_user = substitute_user_col.find_one({"user_id": user["_id"]})
        if substitute_user is not None and substitute_user["enable"] is True:
            zcnt_all_D+=1



    content = str(daily_flag)+"\t"+str(cnt) + "\t" + str(scnt) + "\t" + str(zcnt_all) + "\t" + str(zcnt_all_D)+ "\t" + str(acnt2)+ "\t" + str(acnt)+ "\t" + str(xcnt)+ "\t" +str(sscnt)+"\t"+ str(acnt2_number)+ "\t" +str(wcnt)+"\t"+str(rcnt)+"\t"+ str(ant_number)+ "\t" + str(xcnt_number)+ "\t" + str(scnt_number) +"\n"

    conn.close()
    return content

if __name__ == "__main__":
    fd = open("ul.txt", "r")
    l = fd.readlines()
    fd.close()
    ul = []
    for u in l:
        ul.append(u.strip())
    #print ul
    now = datetime.datetime.now()
    year = now.year
    month=now.month
    day=now.day

    start = datetime.datetime(year, month, day)

    daily = (start - datetime.timedelta(hours=32), start - datetime.timedelta(hours=8))
    daily_flag=(start - datetime.timedelta(hours=24)).strftime('%y年%m月%d日')
    # daily_list = []
    # while (start  < now):
    #     daily = (start - datetime.timedelta(hours=8), start + datetime.timedelta(hours=16))
    #     daily_list.append(daily)
    #     start = start + datetime.timedelta(hours=24)
    

    content = "本日\t新增注册用户数\t新增代运营用户数\t累计注册用户数\t累计注册代运营用户数\t有发车操作的用户数\t有发车操作的用户中的新增用户数\t有发车操作的用户中的代运营用户数\t新增代运营用户有发车的用户\t总发车数量\t当日累计车源总量\t当日在售车源总量\t新增用户发车数量\t代运营用户发车数量\t新增代运营用户发车数量" + "\n"
    #for daily in daily_list:

        #print daily,'\t'
    content += statistics_daily(daily, ul,daily_flag)

    send_mail(content,daily_flag)
