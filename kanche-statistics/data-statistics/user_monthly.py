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

        acnt2:有发车操作的用户数
        acnt:有发车操作的新增用户数
        xcnt:有发车操作的用户中的代运营用户数




'''
def send_mail(content,month_flag):
    month_flag=month_flag+"-月统计"
    month_flag=base64.encodestring(month_flag).split('\n')[0]
    smtp = smtplib.SMTP()
    smtp.connect("smtp.exmail.qq.com", "25")
    smtp.login('junwei.zhuang@kanche.com', 'zhuangjunwei12')
    smtp.sendmail('junwei.zhuang@kanche.com', 'dennis.zhao@kanche.com',
                  'From: junwei.zhuang@kanche.com\r\n' +
                  'To: dennis.zhao@kanche.com\r\n' +
                  'Content-Type: text/plain; charset=UTF-8\r\n' +
                  'Content-Transfer-Encoding: quoted-printable\r\n' +
                  'Subject: =?UTF-8?B?'+month_flag+'?=\r\n\r\n' +
                  quopri.encodestring(content))
    smtp.quit()

def statistics_month(year,month, ul,month_flag):
    conn = pymongo.Connection('127.0.0.1', tz_aware=True)
    db = conn['kanche']
    user_col = db['user']
    vehicle_col = db['vehicle']
    substitute_user_col = db['substitute_user']
    area_col=db['area']
    if month==12:
        start = datetime.datetime(year-1, month, 1)-datetime.timedelta(hours=8)
    else:
        start = datetime.datetime(year, month, 1)-datetime.timedelta(hours=8)
    if month==12:

        stop = datetime.datetime(year,1, 1)-datetime.timedelta(hours=8)
    else:
        stop = datetime.datetime(year, month + 1, 1)-datetime.timedelta(hours=8)
    all_users = user_col.find({"$and": [{"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}, {"mobile": {"$nin": ul}},{"address.city_code":{"$nin":["",None]}}]})

    cnt = 0  #  每个新增用户
    scnt = 0 #每个月新增的代运营用户
    acnt = 0    #2 每个月新增的用户中发车的用户
    dict_acnt_city={}      #新增用户发车数量  city
    dict_cnt_city={}     #新增注册用户数  city
    dict_scnt_city={}    #新增代运营用户数 city
    for user in all_users:

        dict_cnt_city=person_city(user,dict_cnt_city,area_col)
                #------------------------------------------------------------------------
        substitute_user = substitute_user_col.find_one({"user_id": user["_id"]})
        if substitute_user is not None and substitute_user["enable"] is True:
            dict_scnt_city=person_city(user,dict_scnt_city,area_col)

                #--------------------------------------
        vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
        if vcnt > 0:
            acnt += 1
            dict_acnt_city=car_city(user,dict_acnt_city,area_col,vcnt)


    dict_acnt2_city={} #1  本月内有发车操作的用户数  ----city
    all_users = user_col.find({"$and": [{"mobile": {"$nin": ul}},{"address.city_code":{"$nin":["",None]}}]})
    all_user=[]
    for i in all_users:
        all_user.append(i)
    for user in all_user:
        vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
        if vcnt > 0:
            dict_acnt2_city=person_city(user,dict_acnt2_city,area_col)


    dict_xcnt_city={}	     #3  本月内有发车操作的用户中的代运营用户数
    #all_users= user_col.find()
    for user in all_user:

        substitute_user = substitute_user_col.find_one({"user_id": user["_id"]})
        if substitute_user is not None and substitute_user["enable"] is True:
            vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
            if vcnt>0:
                dict_xcnt_city=person_city(user,dict_xcnt_city,area_col)



    dict_acnt2_car_city={}
    dict_xcnt_car_city={}
    for user in all_user:
        vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
        if vcnt>0:
            dict_acnt2_car_city=car_city(user,dict_acnt2_car_city,area_col,vcnt)

            substitute_user = substitute_user_col.find_one({"user_id": user["_id"]})
            if substitute_user is not None and substitute_user["enable"] is True:
                vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$gt": start}}, {"create_at": {"$lt": stop}}]}).count()
                if vcnt>0:
                    dict_xcnt_car_city=car_city(user,dict_xcnt_car_city,area_col,vcnt)




    all_users_ALL = user_col.find({"$and": [ {"create_at": {"$lt": stop}}, {"mobile": {"$nin": ul}},{"address.city_code":{"$nin":["",None]}}]})
    all_user_ALL=[]
    for i in all_users_ALL:
        all_user_ALL.append(i)

    dict_zcnt_all_city={} #累计注册用户数  ----city
    dict_zcnt_all_D_city={} #累计注册代运营用户数 ----city
    dict_wcnt_car_city={}  #当日累计车源总量  ---------city
    dict_rcnt_car_city={}   #当日在售车源总量  --------city
    for user in all_user_ALL:
        dict_zcnt_all_city=person_city(user,dict_zcnt_all_city,area_col)
        vcnt = vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$lt": stop}}]}).count()
        if vcnt>0:
            dict_wcnt_car_city=car_city(user,dict_wcnt_car_city,area_col,vcnt)
        vcnt= vehicle_col.find({"$and": [{"user_id": user["_id"]}, {"create_at": {"$lt": stop}},{"status.offline":False}]}).count()
        if vcnt>0:
            dict_rcnt_car_city=car_city(user,dict_rcnt_car_city,area_col,vcnt)

        substitute_user = substitute_user_col.find_one({"user_id": user["_id"]})
        if substitute_user is not None and substitute_user["enable"] is True:
            dict_zcnt_all_D_city=person_city(user,dict_zcnt_all_D_city,area_col)









    content=''
    for k,v in dict_zcnt_all_city.items():

        content+=k


    if dict_cnt_city.has_key(k):content+="\t"+str(dict_cnt_city[k])
    else:content+="\t"+"0"
    if dict_scnt_city.has_key(k):content+="\t"+str(dict_scnt_city[k])
    else:content+="\t"+"0"
    if dict_zcnt_all_city.has_key(k):content+="\t"+str(dict_zcnt_all_city[k])
    else:content+="\t"+"0"
    if dict_zcnt_all_D_city.has_key(k):content+="\t"+str(dict_zcnt_all_D_city[k])
    else:content+="\t"+"0"
    if dict_acnt2_city.has_key(k):content+="\t"+str(dict_acnt2_city[k])
    else:content+="\t"+"0"
    if dict_xcnt_city.has_key(k):content+="\t"+str(dict_xcnt_city[k])
    else:content+="\t"+"0"
    if dict_acnt2_car_city.has_key(k):content+="\t"+str(dict_acnt2_car_city[k])
    else:content+="\t"+"0"
    if dict_wcnt_car_city.has_key(k):content+="\t"+str(dict_wcnt_car_city[k])
    else:content+="\t"+"0"
    if dict_rcnt_car_city.has_key(k):content+="\t"+str(dict_rcnt_car_city[k])
    else:content+="\t"+"0"
    if dict_xcnt_car_city.has_key(k):content+="\t"+str(dict_xcnt_car_city[k])
    else:content+="\t"+"0"
    if dict_acnt_city.has_key(k):content+="\t"+str(dict_acnt_city[k])+"\n"
    else:content+="\t"+"0"+"\n"




    conn.close()
    return content




def person_city(user,dict_city,area_col):


    if user["address"]["province_code"] in['110000','120000','310000','500000']:
        city=area_col.find_one({'code':user["address"]["province_code"]},{'name':1})

        if dict_city.has_key(city['name']):
            dict_city[city['name']]+=1
        else:
            dict_city[city['name']]=1
    else:
        #print user['_id'],'######'
        #print user["address"]["city_code"],'$$$'
        city=area_col.find_one({'code':user["address"]["city_code"]},{'name':1})
        #print city['_id'],'######'
        #print city['name'],'@@@'
        if dict_city.has_key(city['name']):
            #print '!!!'
            dict_city[city['name']]+=1
        else:
            dict_city[city['name']]=1
    return dict_city
def car_city(user,dict_city,area_col,vcnt):
    if user["address"]["province_code"] in['110000','120000','310000','500000']:
        city=area_col.find_one({'code':user["address"]["province_code"]},{'name':1})

        if dict_city.has_key(city['name']):
            dict_city[city['name']]+=vcnt
        else:
            dict_city[city['name']]=vcnt
    else:
        city=area_col.find_one({'code':user["address"]["city_code"]},{'name':1})
        if dict_city.has_key(city['name']):
            dict_city[city['name']]+=vcnt
        else:
            dict_city[city['name']]=vcnt
    return dict_city


if __name__ == "__main__":
    fd = open("ul.txt", "r")
    l = fd.readlines()
    fd.close()
    ul = []
    for u in l:
        ul.append(u.strip())


    now = datetime.datetime.now()
    month=now.month
    if month==1:
        month=12

    else:
        month=month-1

    year=now.year
    month_flag=str(month)+"月"

    content = "本月\t新增注册用户数\t新增代运营用户数\t累计注册用户数\t累计注册代运营用户数\t有发车操作的用户数\t有发车操作的用户中的代运营用户数\t总发车数量\t本月累计车源总量\t本月在售车源总量\t代运营用户发车数量\t新增用户发车数量" + "\n"

    content += statistics_month(year,month, ul,month_flag)

    send_mail(content,month_flag)

