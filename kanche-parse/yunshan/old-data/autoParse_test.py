#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pymongo,signal, sys, os, autoParse, datetime, time
from multiprocessing import Process


reload(sys)
sys.setdefaultencoding('utf-8')

global  maxJob

maxJob = 8
maxRows = 500

def echo(pStr):
    print '----------------------------------------------\n',pStr,'\n----------------------------------------------'
def mark():
    echo(datetime.datetime.now())

class Watcher:  
    def __init__(self):  
        self.child = os.fork()  
        if self.child == 0:  
            return  
        else:  
            self.watch()  
  
    def watch(self):  
        try:  
            os.wait()  
        except KeyboardInterrupt:  
            print 'KeyBoardInterrupt'  
            self.kill()  
        sys.exit()  
  
    def kill(self):  
        try:  
            os.kill(self.child, signal.SIGKILL)  
        except OSError: pass
        
def getOne(pycur):
    for o in pycur:
        return o
    return None
        
def job(data,data1,data4):
    if data == None:return False
    try:
       iData=autoParse.AutoParser(data,data1,data4).getAll()
    except Exception as e:
        id = data['_id']
        echo((id,e))
        return True
    
    
    #print data['_id']
    nData={}
    date={}
    flag={}
    status={}
    #车源ID
    nData['vehicle_id']=iData['pageId']
    nData['url']=iData['url']
    #标题
    nData['title']=iData['title']
    #城市ID
    nData['city_id']=iData['cityId']
    #全局车型ID
    nData['global_model_id']=None
    #局部车型ID
    nData['local_model_id']=iData['modelId']if iData['modelId'] else None
    #发布日期
    date['release_date']=datetime.datetime.strptime(iData['pubDate'],"%Y-%m-%d") if iData['pubDate'] else None
    if date['release_date']:flag['release_date_day_exsits']=True
    else:flag['release_date_day_exsits']=False

    #初登日期
    date['register_date']=datetime.datetime.strptime(iData['firstRegistrationDate'],"%Y-%m-%d")if iData['firstRegistrationDate'] else None
    if date['register_date']:flag['register_date_day_exsits']=True
    else:flag['register_date_day_exsits']=False

    #公里数
    nData['mileage']=iData['mileage'] if iData['mileage'] else None
    #外观颜色
    nData['basic_outer_color_name']=iData['exteriorColor']if iData['exteriorColor']else None
    nData['basic_outer_color_id']=iData['exteriorColorId']if iData['exteriorColorId']else None

    #内饰颜色

    nData['interior_color_type']=iData['interiorColor']if iData['interiorColor']else None

    #排放标准
    nData['emmission_standard']=iData['emissionStandard']if iData['emissionStandard']else None

    #车架号
    nData['vin']=None

    #原车用途
    nData['purpose']=iData['carUsage']if iData['carUsage']else None

    #过户次数
    nData['trade_times']=int(iData['transferTimes']) if iData['transferTimes'] else None

    #年检
    date['inspection_expire_date']=datetime.datetime.strptime(iData['inspectionOfValidity'],"%Y-%m-%d") if iData['inspectionOfValidity'] else None
    if date['inspection_expire_date']:flag['inspection_expired']=True
    else:flag['inspection_expired']=False


    if date['inspection_expire_date']:flag['inspection_expire_date_day_exsits']=True
    else:flag['inspection_expire_date_day_exsits']=False


    #车船税
    date['vehicle_tax_expire_date']=datetime.datetime.strptime(iData['vehicleAndVesselTax'],"%Y-%m-%d") if iData['vehicleAndVesselTax'] else None
    if date['vehicle_tax_expire_date']:flag['vehicle_tax_expired']=True
    else:flag['vehicle_tax_expired']=False
    if date['vehicle_tax_expire_date']:flag['vehicle_tax_expire_date_day_exsits']=True
    else:flag['vehicle_tax_expire_date_day_exsits']=False

    #交强险
    #print iData['compulsoryInsurance'],'*'
    date['compulsory_insurance_expire_date']=datetime.datetime.strptime(iData['compulsoryInsurance'],"%Y-%m-%d") if iData['compulsoryInsurance'] else None
    if date['compulsory_insurance_expire_date']: flag['compulsory_insurance_expired']=True
    else:flag['compulsory_insurance_expired']=False


    if date['compulsory_insurance_expire_date']:flag['compulsory_insurance_expire_date_day_exsits']=True
    else:flag['compulsory_insurance_expire_date_day_exsits']=False


    #商业险
    date['commercial_insurance_expire_date']=datetime.datetime.strptime(iData['businessInsExpDate'],"%Y-%m-%d") if iData['businessInsExpDate'] else None
    if date['commercial_insurance_expire_date']:flag['commercial_insurance_expired']=True
    else:flag['commercial_insurance_expired']=False

    if date['commercial_insurance_expire_date']:flag['commercial_insurance_expire_date_day_exsits']=True
    else:flag['commercial_insurance_expire_date_day_exsits']=False

    #质保到期
    date['warranty_expire_date']=datetime.datetime.strptime(iData['warrantyDate'],"%Y-%m-%d")if iData['warrantyDate'] else None
    if date['warranty_expire_date']:flag['warranty_expired']=True
    else:flag['warranty_expired']=False

    if date['warranty_expire_date']:flag['warranty_expire_date_day_exsits']=True
    else:flag['warranty_expire_date_day_exsits']=False


    #购物发票
    if iData['vehiclePurchaseInvoice']:
        status['purchase_invoice_exists']=True
    else:
        status['purchase_invoice_exists']=False
    #登记证
    if iData['registration']:
        status['registration_certificate_exists']=True
    else:
        status['registration_certificate_exists']=False

    #行使证
    if iData['drivingLicense']:
        status['vehicle_license_exists']=True
    else:
        status['vehicle_license_exists']=False

    #保养记录
    if iData['maintainceRecords']:status['maintenance_record_exists']=True
    else:status['maintenance_record_exists']=False
    #全局车商
    nData['golbal_dealer_id']=None
    #局部车商
    nData['local_dealer_id']=iData['dealerId']if iData['dealerId'] else None
    #车主姓名
    nData['owner_name']=iData['sellerName']if iData['sellerName']else None                                 #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #车主电话
    nData['owner_mobile']=iData['phoneCode'] if iData['phoneCode']else None
    #车主电话图片url
    nData['owner_mobile_image_url']=iData['telphoneImageURL']if iData['telphoneImageURL']else None
    #备注
    nData['description']=iData['comments']if iData['comments']else None
    #网站ID
    nData['website_id']=iData['siteId']
    #原始网站ID
    nData['original_website_id']=None                          #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #车辆图片网址
    nData['vehicle_image_url']=iData['imageURL']if iData['imageURL']else None
    #价格 （非空）
    nData['price']=int(float(iData['price'])*10000)
    #print nData['price']
    #采集日期
    nData['collect_at']=iData['gatherDate']if iData['gatherDate'] else None

    #最新更新日期
    create_at=time.strftime('%Y-%m-%d',time.localtime(time.time()))
    nData['create_at']=datetime.datetime.strptime(create_at,"%Y-%m-%d")
    nData['update_at']=None
    nData['website_update_date']=None
    if nData['website_update_date']:flag['website_update_date_day_exists']=True
    else :flag['website_update_date_day_exists']=False
    #状态
    nData['vehicle_status']=None


    dedup={}
    dedup['local_vehicle_deduplication_flag']=0
    dedup['global_vehicle_deduplication_flag']=0
    dedup['local_vehicle_identity_id']=None
    dedup['global_vehicle_identity_id']=None
    dedup['local_class_span']=float(0)
    dedup['global_class_span']=float(0)
    dedup['local_deduplication_count']=0
    dedup['global_deduplication_count']=0
    #异常标记
    flag['is_exception']=None
    dedup['local_deduplication_process_flag']=None
    dedup['global_deduplication_process_flag']=None
    flag['is_delete']=False

    #===========================================

    nData['dedup']=dedup
    nData['flag']=flag
    nData['date']=date
    nData['status']=status
    #print 'OK'

    base_vehicle_source_local=db.base_vehicle_source_local
    base_vehicle_source_local.insert(nData)
    echo(data['_id'])
        
if __name__ == "__main__":
    Watcher()
    '''
    conn = MySQLdb.Connect(host='115.29.109.138', user='root', passwd='7ujmko0', db='water',charset='utf8')


    cur = conn.cursor()
    sqlStr = "SELECT cityId, cityName FROM base_city_copy"
    cur.execute(sqlStr)
    cityData = list(cur.fetchall())
    cur.close()
    
    curColor=conn.cursor()
    sqlStr="SELECT id,colorName FROM base_color"
    curColor.execute(sqlStr)
    colorData=list(curColor.fetchall())
    curColor.close()
    
    conn.close()
    '''
    conn = pymongo.Connection()
    db = conn.kkcrawler
    db2 = conn.water
    Data=db2.base_city.find()
    cityData=[]
    for i in Data:
	x=(i['cityId'],i['cityName'])
	cityData.append(x)
    Data=db2.base_color.find()
    colorData=[]
    for i in Data:
	x=(i['id'],i['colorName'])
	colorData.append(x)
    
    iData = db.ocarSrcContent.find({}).sort([('_id',pymongo.ASCENDING)]).limit(maxRows)
    iObj = getOne(iData)
    
    iJobLst = [None for i in range(0,maxJob)]
    
    while iObj:
        for i in range(0,maxJob):
            p = iJobLst[i]
            if p:
                if p.exitcode != None:
                    id = iObj['_id']
                    p = Process(target=job, args=(iObj, cityData, colorData))
                    p.start()
                    iJobLst[i] = p
                    
                    iData = db.ocarSrcContent.find({'_id':{'$gt':id}}).sort([('_id',pymongo.ASCENDING)]).limit(maxRows)
                    iObj = getOne(iData)
                    break
            else:
                id = iObj['_id']
                p = Process(target=job, args=(iObj, cityData, colorData))
                p.start()
                iJobLst[i] = p
                
                iData = db.ocarSrcContent.find({'_id':{'$gt':id}}).sort([('_id',pymongo.ASCENDING)]).limit(maxRows)
                iObj = getOne(iData)
                break
                
    for p in iJobLst:
        if p:
            if p.exitcode != None:
                p.join()
    
    echo('ok')

