# -*- coding: utf-8 -*-
__author__ = 'zhuangjunwei'
import re, json, chardet, random
from datetime import datetime, timedelta
from scrapy.selector import Selector
import traceback


import sys

reload(sys)
sys.setdefaultencoding('utf-8')


def echo(pStr):
    print '----------------------------------------------'
    print pStr
    print '----------------------------------------------'


class AutoParser():
    def __init__(self,pData,cityData,colorData):
        self.colorData=colorData
        self.cityData=cityData
        self.data = pData
        self.gatherDate = pData['created']        
        self.html = pData['content']
        self.hxs = Selector(text=self.html, type="html")    
    
        iTmp = self.hxs.xpath(u'//*[text()="分享" or contains(text(),"鉴定")]')
        if len(iTmp):
            self.summaryBox = self.getSummaryBox(iTmp[0])
        else:
            self.summaryBox = self.hxs.xpath('/html/body')
    
    #字典排序
    def sortByValue(self, pDict):
            r = []
            items=pDict.items() 
            if len(items):
                backitems = []
                if isinstance(items[0][1], int):
                    backitems=[(v[1],v[0],v[1]) for v in items]
                else:
                    backitems=[(len(v[1]),v[0],v[1]) for v in items]
                    
                backitems.sort(lambda a,b :-cmp(a[0],b[0]))
                r = backitems
            return r
            
    #获取节点标签名
    def getTagName(self,pNode):
        s = pNode.extract()
        nodeTag = re.compile(r'<([^>\s]+)').findall(s)

        if len(nodeTag):
            clsStr = pNode.xpath('@class').extract()

            if len(clsStr):
                return nodeTag[0],'[@class="%s"]'%clsStr[0]
            else:
                return nodeTag[0],''
        else:
            return ''
            
    #获取节点xpath
    def getXpath(self,pNode,pList):
        rNode = pNode.xpath('./..')[0]
        tagName = self.getTagName(rNode)
        if tagName[0] in ['','body']:
            return u'//%s'%('/'.join(pList))
        else:
            pList.insert(0,''.join(tagName))
            return self.getXpath(pNode.xpath('./..'),pList)
            
    #获取车源概述
    def getSummaryBox(self, pNode):
        iNode = pNode.xpath('./..')[0]
        if u'万公里' in iNode.extract() and len(iNode.xpath('.//img')):
            return iNode
        else:
            return self.getSummaryBox(iNode)
        
    # 发布时间
    def parseDate(self, pTxt, pDate):
        iTxt = pTxt
        iResult = ''
        if iTxt.find(u'前') > -1:
            iTmp = int(re.findall('(\d+)', iTxt)[0])
            if iTxt.find(u'秒') > -1:
                iInterval = timedelta(seconds=iTmp)
            elif iTxt.find(u'分钟') > -1:
                iInterval = timedelta(minutes=iTmp)
            elif iTxt.find(u'小时') > -1:
                iInterval = timedelta(hours=iTmp)
            elif iTxt.find(u'天') > -1:
                iInterval = timedelta(days=iTmp)
            elif iTxt.find(u'月') > -1:
                iInterval = timedelta(days=iTmp * 30)
            elif iTxt.find(u'星期') > -1:
                iInterval = timedelta(weeks=iTmp)
            elif iTxt.find(u'周') > -1:
                iInterval = timedelta(weeks=iTmp)
            else:
                iInterval = timedelta(days=100 * 365)
            iResult = pDate - iInterval
            iResult = '%s-%s-%s' % (iResult.year, iResult.month, iResult.day)
        elif len(re.findall('\d{4}', iTxt)):
            iTmp = re.findall('(\d{4})[^\d]?(\d{2})[^\d]?(\d+)', iTxt)
            if len(iTmp):
                iResult = '%s-%s-%s' % iTmp[0]
            else:
                iTmp = re.findall('(\d{4})[^\d]?(\d+)', iTxt)
                if len(iTmp):
                    iResult = '%s-%s-01' % iTmp[0]
        elif len(re.findall('\d{2}-\d{2}', iTxt)):
            iTmp = re.findall('(\d{2})-(\d{2})', iTxt)
            if len(iTmp):
                iResult = str(pDate.year)+('-%s-%s' % iTmp[0])
                
        return iResult


    # 详情页网址
    def getUrl(self):
        iResult = self.data['url'].split('#')[0].split('?')[0]
        return iResult


    #车源ID
    def getPageId(self):
        iResult = ''
        iNodeList = self.data['url'].split('.')[-2].split('/')[-1]
        iTmp = re.findall('\d+', iNodeList)
        if len(iTmp):
            iResult = iTmp[0]
        return iResult


    #标题
    def getTitle(self):
        iResult = ''
        iNodeList = self.hxs.xpath('//h1 | //h2 | //h3')
        for iItem in iNodeList:
            iTxt = ' '.join(iItem.xpath('text()').extract()).strip()
            iTxt = iTxt.strip()
            if len(re.findall(u'(\d{2,4})款', iTxt)):

                iResult = iTxt
                break
            else:
                iTmp = iItem.xpath('*/text()').extract()

                if len(iTmp):
                    iTxt = iTmp[0].strip()
                    if len(re.findall('\d{4}', iTxt)):
                        iResult = iTxt
                        break
        return iResult


    #车型ID
    def getModelId(self):
        iResult = '0'
        try:
            iNodeList = self.hxs.xpath('//input[@type="hidden"]')
            for iItem in iNodeList:
                iTmp = iItem.xpath('@id').extract()[0].lower()
                if iTmp.find('id') > -1:
                    if iTmp.find('trim') > -1 or iTmp.find('spec') > -1 or (
                            iTmp.find('car') > -1 and iTmp.find('ucar') < 0):
                        iResult = iItem.xpath('@value').extract()[0]
                        break
            if iResult == '':
                iNodeList = re.findall('\?vehicleKey=([^"]+)', self.html)
                if len(iNodeList): iResult = iNodeList[0]
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = '0'
        return iResult


    #车商ID
    def getDealerId(self):
        iResult = '0'
        try:
            iNodeList = self.hxs.xpath(u'//a[contains(text(),"进入") and contains(text(),"店")]/@href').extract()
            if len(iNodeList):
                iTxt = iNodeList[0].split('/')[-1]
                iTmp = re.findall('\d+', iTxt)
                if len(iTmp):
                    iResult = iTmp[0]
                else:
                    iTxt = iNodeList[0].split('/')[-2]
                    iTmp = re.findall('\d+', iTxt)
                    if len(iTmp):
                        iResult = iTmp[0]
                    else:
                        iResult = '0'
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = '0'
        return iResult


    #发布更新时间

    def getPubDate(self):
        iResult = ''
        try:
            flag = True
            if 'pubDate' in self.data.keys():
                iTxt = self.data['pubDate'].strip()
                if len(iTxt):
                    iResult = self.parseDate(iTxt, self.gatherDate)
                    flag = False
                    
            if flag:
                iNodeList = self.hxs.xpath(u'//*[contains(text(),"发布") or contains(text(),"更新")]/text()').extract()
                for iTxt in iNodeList:
                    if len(re.findall('\d+', iTxt)):
                        iTxt = iTxt.replace(u'发布', '').replace(u'更新', '').strip()
                        iResult = self.parseDate(iTxt, self.gatherDate)
                        if iResult != '': break
            '''
            if iResult == '':
            :q    iNodeList = self.shxs.xpath('//*/text()').extract()
                for i in xrange(len(iNodeList)-1,-1,-1):
                    iTxt = iNodeList[i]
                    if len(re.findall('\d+', iTxt)) and (iTxt.find(u'前') or len(re.findall('\d{4}', iTxt))):
                        iResult = self.parseDate(iTxt, self.gatherDate)
                        if iResult != '':break
            '''
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult


    #价格
    def getPrice(self):
        iResult = ''
        try:
            iTitle = self.getTitle()
            iNodeList = self.hxs.xpath(u'//body//*[contains(*,"万")]')
            for iItem in iNodeList:
                #print iItem.extract(),'&&&&&'
                iSubList = iItem.xpath('..//*/text() | ../..//*/text()').extract()
                for iSub in iSubList:
                    if iSub != '' and iSub.find(u'公里') == -1:
                        iSub = iSub.replace(u'¥', '').replace(u'万', '').strip()
                        iTmp = re.findall('^\d+(?:\.\d+)?$', iSub)
                        if len(iTmp):
                            if len(iTmp[0]) < 8:
                                iResult = iTmp[0]
                                break
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        #print iResult
        return iResult


    #里程数
    def getMileage(self):
        iResult = 0
        try:
            iNodeList = self.hxs.xpath(u'//*[contains(text(),"万公里")]')

            for iItem in iNodeList:
                iTmp = ' '.join(iItem.xpath(u'../*/text()').extract()).strip()
                iTmp = re.findall(u':?(\d+\.\d+)万公里', iTmp)
                if len(iTmp):
                    iResult = int(float(iTmp[0]) * 10000)
            return iResult
        except:
            iResult = 0

    #初登日期
    def getFirstRegistrationDate(self):
        iResult = ''

        iNodeList = self.hxs.xpath(u'//text()[contains(.,"上牌")]/../..')
        for iItem in iNodeList:
            iTmp = iItem.xpath('text() | */text()').extract()
            iTxt = ''.join(iTmp).strip()
            iTmp = re.findall(u'(\d{4}年\d{1,2}月)', iTxt)
            if len(iTmp):
                iResult = iTmp[0].replace(u'年', '-').replace(u'月', '-') + '01'
                break
        return iResult


    #原车用途
    def getCarUsage(self):
        iResult = ''

        iNodeList = self.hxs.xpath(u'//text()[contains(.,"用") and contains(.,"途")]/../..')
        for iItem in iNodeList:
            iTmp = iItem.xpath('text() | */text()').extract()

            iTxt = re.sub(u'用[ \s　]*途', u'用途', '\n'.join(iTmp).strip())
            if iTxt.find(u'用途') > -1:
                iTxt = re.split(u'用途\s*[:：]?\s*', iTxt)[1].split('\n')[0]
                iResult = iTxt
                break

        if iResult == '':
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"车辆类型")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = '\n'.join(iTmp).strip()
                iTxt = re.split(u'类型\s*[:：]?\s*', iTxt)[1].split('\n')[0]
                iResult = iTxt
                break
        return iResult


    #外观颜色

    def getExteriorColor(self):
        iResult = ''
        self.color=''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"颜") and contains(.,"色") or contains(.,"颜色")]/../..')
            if iNodeList:
                for iItem in iNodeList:
                    iTmp = iItem.xpath('text() | */text()').extract()
                    iTxt = ' '.join(iTmp).strip()
                    color = re.compile(u'色[:：]?\s*([\u4e00-\u9fa5\-]+)').findall(iTxt)
                    if color:
                        
                            self.color = color[0]
                            iResult = color[0]
            else:
                self.color = ''
                iResult = self.color
            if self.color:                                    
                colorId=''
                for i in self.colorData:
                    if i[1]==self.color:
                        colorId=int(i[0])
                        self.corlorId=colorId
                        break
                if colorId:pass
                else:self.corlorId=14
            else:
                self.corlorId = 15
        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"                
                self.corlorId = ''
                iResult = ''
        return iResult


    #内饰颜色
    def getInteriorColor(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"颜色") and contains(.,"颜") and contains(.,"色")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=' '.join(iTmp).strip()
                if iTxt:
                    if iTxt.find(u"深") >= 0:
                        iResult = "deep"
                        break
                    elif iTxt.find(u"浅") >= 0:
                        iResult = "light"
                        break
                        #light/deep                
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult

    #城市
    def getCity(self):
        iResult = ''
        iCityData = self.cityData
        
        province = ''
        city = ''

        iFlag = False
        iTmp = self.hxs.xpath('/html/head/meta[@name="location"]/@content')
        if len(iTmp):
            iTxt = iTmp[0].extract()
            iTmp = re.findall('province\s*=\s*([^;]+);\s*city\s*=\s*([^;]+)',iTxt)
            if len(iTmp):
                province = iTmp[0][0].strip()
                city = iTmp[0][1].strip()
            else:
                iFlag = True
        else:
            iFlag = True
            
        if iFlag:
            iTmp = self.hxs.xpath('/html/head/meta[@name="keywords" or @name="description"]/@content').extract()
            if len(iTmp):
                iTmp = re.split(u'，|,',','.join(iTmp))
                iDict = {}
                for i in iTmp:
                    if (u'二手车' in i or u'二手' in i) and i.find(u'二手')>1:
                        iTxt = i.split(u'二手')[0]
                        if iTxt in iDict.keys():
                            iDict[iTxt] += 1
                        else:
                            iDict[iTxt] = 1
                iDict = self.sortByValue(iDict)
                if len(iDict):
                    city = iDict[0][1]
        
        cityId=0
        if city !='':
            for i in iCityData:
                if city in i[1]:
                    cityId=int(i[0])
                    break
        self.cityId=cityId
        
        iResult = city
        return iResult
    
    #看车地址
    def getAddress(self):
        iResult = ''
        
        iLst = []
        iNodeList = self.summaryBox.xpath(u'.//*[contains(text(),"看车地") or contains(@class,"dress") or contains(@id,"dress")]/..')
        for iTmp in iNodeList:
            for iItem in iTmp.xpath('text()|.//text()'):
                iTxt = iItem.extract().strip()
                iTxt = re.sub(u'【[^】]+】','',iTxt).replace(u'看车地','')
                if re.sub('[\d \-]','',iTxt)!='' and len(iTxt)>4:
                    iLst.append(iTxt)
            
        iResult = '\n'.join(iLst)
        return iResult
        
    #排放标准
    def getEmissionStandard(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"环保标准")]/../.. | @title[contains(.,"排放标准")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                #iResult = iTmp
                for i, element in enumerate(iTmp):
                    if element.find(u"国") >= 0 or element.find(u"欧") >= 0 or element.find(u"京") >= 0:
                        if element.find(u'：') >= 0:
                            iResult = element.split('：')[1]
                        else:
                            iResult = element
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult


    #质保
    def getWarrantyDate(self):
        iResult = ''
        try:

            

            iNodeList = self.hxs.xpath(u'//text()[contains(.,"质保")]/../..')


            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = ''.join(iTmp).strip()
                zhibao=re.findall(u'质保[^\d]*(\d{4})[^\d](\d{1,2})',iTxt)
                if zhibao:
                    zhibao='%s-%s-%s' % (zhibao[0][0],zhibao[0][1],'01')
                    iResult=zhibao
                    break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''

        return iResult
    #交强险


    def getCompulsoryInsurance(self):
        iResult = ''
        try:

            iNodeList = self.hxs.xpath(u'//text()[contains(.,"交强险") or contains(.,"保险")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=''.join(iTmp).strip()
                baoxian=re.findall(u'交强险[^\d]*(\d{4})[^\d](\d{1,2})|保险到[^\d]*(\d{4})[^\d](\d{1,2})',iTxt)

                if baoxian:
                    if len(baoxian[0][0]):
                        baoxian='%s-%s-%s' % (baoxian[0][0],baoxian[0][1],'01')

                        #print baoxian,'***********************'
                        iResult=baoxian
                        break
                    else:
                        baoxian='%s-%s-%s'%(baoxian[0][2],baoxian[0][3],'01')
                        #print baoxian,'*********************'
                        iResult=baoxian
                        break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        return iResult


    #商业险
    def getBusinessInsExpDate(self):
        iResult = ''
        try:

            iNodeList = self.hxs.xpath(u'//text()[contains(.,"商业险")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = ' '.join(iTmp).strip()
                business=re.findall(u'商业险[^\d]*(\d{4})[^\d]*(\d{1,2})',iTxt)
                if business:
                    #print business,'%%%%%%%%%%%%%%'
                    business='%s-%s-%s'%(business[0][0],business[0][1],'01')
                    #print business,'%%%%%%%%%%%%%%%%%%'
                    iResult=business
                    break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        return iResult


    #年检
    def getInspectionOfValidity(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"年检") or contains(.,"年审")]/../..')

            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = ' '.join(iTmp).strip()
                #print iTxt,'^^^^^^^^^^^^^^^'
                nianjian=re.findall(u'年[^\d]*(\d{4})[^\d]*(\d{1,2})',iTxt)
                if nianjian:
                    if len(nianjian[0][1])==2:
                        #print nianjian[0],'$$$$$$$$$$$$$$'
                        nianjian='%s-%s-%s' % (nianjian[0][0],nianjian[0][1],01)
                        iResult=nianjian
                    else:
                        month='0'+nianjian[0][1]
                        nianjian='%s-%s-%s' % (nianjian[0][0],month,'01')
                        iResult=nianjian
                    break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        return iResult


    #车船税
    def getVehicleAndVesselTax(self):
        iResult = ''
        try:

            iNodeList = self.hxs.xpath(u'//text()[contains(.,"车船") and contains(.,"税")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = ' '.join(iTmp).strip()
                #print iTxt,'^^^^^^^^^^^^^^^'

                chechuan=re.findall(u'车船[^\d]*(\d{4})',iTxt)
                if chechuan:
                    #print chechuan,'(((((('
                    chechuan='%s-%s-%s'%(chechuan[0],'01','01')
                    #print chechuan,'&&&&&&&&&&&&&'
                    iResult=chechuan
                    break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''

        return iResult


    #登记证
    def getRegistration(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"登记证")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=''.join(iTmp).strip()
                #print iTxt,'&&&&&&&&&&&&&&&&&&'
                iTvl=re.findall(u'登记证[^\w]*([\u4e00-\u9fa5\-]+)',iTxt)
                #print iTvl[0],'*******************'
                if iTvl:
                    if u'全'in iTvl[0]:
                        iResult=True
                        break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        return iResult


    #行驶证
    def getDrivingLicense(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"行驶证")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=''.join(iTmp).strip()
                #print iTxt,'&&&&&&&&&&&&&&&&&&'
                iTvl=re.findall(u'行驶证[^\w]*([\u4e00-\u9fa5\-]+)',iTxt)
                #print iTvl[0],'*******************'
                if iTvl:
                    if u'全'in iTvl[0]:
                        iResult=True
                        break


        except Exception as e:
                    print e
                    print "======================"
                    traceback.print_exc(file=sys.stdout)
                    print "======================"

                    iResult = ''
        return iResult


    #购车发票
    def getVehiclePurchaseInvoice(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"购车发票")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=''.join(iTmp).strip()
                #print iTxt,'&&&&&&&&&&&&&&&&&&'
                iTvl=re.findall(u'购车发票[^\w]*([\u4e00-\u9fa5\-]+)',iTxt)
                #print iTvl[0],'*******************'
                if iTvl:
                    if u'全'in iTvl[0]:
                        iResult=True
                        break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        return iResult


    #过户次数
    def getTransferTimes(self):
        iResult = 0
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"过户次数")]/../..')

            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | *//text()').extract()
                iTxt=''.join(iTmp).strip()
                #print iTxt,'***************'
                iTvl=re.findall(u'过户[^\d]*(\d{1,2})',iTxt)
                #print iTvl,'%%%%%%%%%%%%%%'
                if iTvl:
                    #print iTvl,'*************'
                    iResult=iTvl[0]
                    break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        return iResult


    #大图地址
    def getImageURL(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(
                u'//text()[contains(.,"保养")]/../../../../following-sibling::* | //text()[contains(.,"年检到期")]/../../../../following-sibling::*')

            for iItem in iNodeList:
                #print iItem.extract(),'JJJJJJJJJJJJJ'


                if iItem.xpath(u'.//img/@src | .//img/@src2 | .//img/@data-original').extract():
                    iTmp = iItem.xpath(u'.//img/@src | .//img/@src2 | .//img/@data-original').extract()
                    #print iTmp,'FFF'
                    ImageURL1 = []
                    for iItem in iTmp:
                        #print type(iItem),'SSSSSSSSSSSSSSSSSSSS'
                        if u'jpg' in iItem:
                            ImageURL1.append(iItem)
                        else:
                            pass
                    iResult=ImageURL1
                    break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        #iResult += ",".join(iItem[0])

        return iResult


    #卖家名称
    def getSellerName(self):
        iResult = ''
        #contains(text(),"linkman")
        iNodeList = self.hxs.xpath(u'.//*[(contains(text(),"联") and contains(text(),"系") and contains(text(),"人")) and not(contains(text(),"工作人员"))]')
        if len(iNodeList):
            iTxt = iNodeList[0].xpath('text()').extract()[0]
            if len(iTxt.replace(u'联','').replace(u'系','').replace(u'人','').replace(u'：','').strip())<2:
                iTmp = iNodeList[0].xpath('./../text()|./..//*/text()').extract()
                iTxt = iTmp[-2] if iTmp[-1].strip()=='' else iTmp[-1]
                iResult = iTxt
            else:
                iTxt = re.sub(u'[】：]','',re.split(u'[ 【]',iTxt.split(u'联系人')[1])[0])
                iResult = iTxt
        else:
            iNodeList = self.hxs.xpath(u'.//*[contains(text(),"linkman")]/text()').extract()
            if len(iNodeList):
                iTxt = iNodeList[0]
                iTxt = re.sub("'",'',iTxt.split('linkman')[1].split(",")[0])
                iResult = iTxt
            else:
                iNodeList = self.summaryBox.xpath(u'.//*[starts-with(text(),"400") or starts-with(text(),"1") or starts-with(text(),"0")]')
                for iItem in iNodeList:
                    iTxt = ''.join(iItem.xpath('text()').extract())
                    iTxt = re.sub('\s','',iTxt).replace('-','')
                    if re.sub('\d','',iTxt)=='' and (len(iTxt) == 11 or (len(iTxt) == 10 and iTxt.find('400')==0)):
                        iTmp = iItem.xpath('./../following-sibling::*[1]/text()|./../following-sibling::*[1]//*/text()').extract()
                        iTxt = ''.join(iTmp)
                        iResult = iTxt
                        
        return iResult

    #卖家电话-数字
    def getPhoneCode(self):
        iTels = []
        iNodeList = self.summaryBox.xpath(u'.//*[starts-with(text(),"400") or starts-with(text(),"1") or starts-with(text(),"0")]')
        for iItem in iNodeList:
            iTxt = ''.join(iItem.xpath('text()').extract())
            iTxt = re.sub('\s','',iTxt).replace('-','')
            #print '+++++++++++++++++++++++++',iTxt,'+++++++++++++++++++++++++'
            if re.sub('\d','',iTxt)=='' and (len(iTxt) == 11 or (len(iTxt) == 10 and iTxt.find('400')==0)):
                iTels.append(iTxt)
                
        return ','.join(iTels)


    #卖家电话-图片
    def getTelphoneImageURL(self):
        iResult = ''
        
        iNodeList = self.summaryBox.xpath(u'.//*[contains(@style,"background-image") and contains(@style,"tel")]/@style')
        
        if len(iNodeList):
            iTxt = iNodeList[0].extract()
            iTxt = iTxt.split("url('")[1].split("'")[0]
            iResult = iTxt
        else:
            iNodeList = self.summaryBox.xpath(u'.//img[contains(@src,"Phone")]/@src')
            if len(iNodeList):
                iTxt = iNodeList[0].extract()
                iResult = iTxt
                
        return iResult


    #车主留言


    def getComments(self):
        iResult = ''
        return iResult
        try:
            iNodeList = self.hxs.xpath(
                u'//text()[contains(.,"保养")]/../../../../following-sibling::* | //text()[contains(., "车辆类型")]/../../../../following-sibling::* | //text()[contains(.,"保养")]/../../../.ollowing-sibling::*[position()=1] ')

            for iItem in iNodeList:
                iTmp = iItem.xpath(u'.//p/text()').extract()
                if iTmp:
                    #print iTmp,'*****'
                    for iTxt in iTmp:
                        #print iTmp,'@@@@@@@@@@@@@@@@@@'

                        if len(iTxt) > 4:
                            iResult = iTxt.replace('-', '').replace('\n', '')
                            break

                    break
                    #iResult=iTmp
                    #break
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult


    #保养记录
    def getMaintainceRecords(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"保养")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                if iTmp[0].find(u"保养") >= 0 and len(iTmp) > 1:
                    iResult = iTmp[1]
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult


    #采集日期
    def getGatherDate(self):
        iResult = self.data['create_at']
        return iResult


    #网站ID

    def getWebSiteId(self):
        iResult = ''
        try:
            WebSiteId = self.getUrl().replace('http://', '').split('/')[0].replace('www.', '')

            iResult = WebSiteId

        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult


    def getAll(self):
        iData = {
            'siteId': self.getWebSiteId(),
            'url': self.getUrl(),
            'pageId': self.getPageId(),
            'title': self.getTitle(),
            'modelId': self.getModelId(),
            'dealerId': self.getDealerId(),

            'pubDate': self.getPubDate(),
            'mileage': self.getMileage(),
            'price': self.getPrice(),
            'firstRegistrationDate': self.getFirstRegistrationDate(),
            'carUsage': self.getCarUsage(),

            'exteriorColor': self.getExteriorColor(), 
            'exteriorColorId': self.corlorId,
            'interiorColor': self.getInteriorColor(),

            'city': self.getCity(),
            'cityId': self.cityId,
            #'district': self.getDistrict(),
            #'province': self.getProvince(),

            'emissionStandard': self.getEmissionStandard(),
            'compulsoryInsurance': self.getCompulsoryInsurance(),
            'businessInsExpDate': self.getBusinessInsExpDate(),
            'inspectionOfValidity': self.getInspectionOfValidity(),
            'vehicleAndVesselTax': self.getVehicleAndVesselTax(),

            'warrantyDate': self.getWarrantyDate(),

            'registration': self.getRegistration(),
            'drivingLicense': self.getDrivingLicense(),
            'vehiclePurchaseInvoice': self.getVehiclePurchaseInvoice(),
            'transferTimes': self.getTransferTimes(),
            'imageURL': self.getImageURL(),

            'sellerName': self.getSellerName(),
            'address':self.getAddress(),
            'phoneCode': self.getPhoneCode(),
            'telphoneImageURL': self.getTelphoneImageURL(),
            'comments': self.getComments(),

            'maintainceRecords': self.getMaintainceRecords(),
            'gatherDate': self.gatherDate
        }
        #for k,v in iData.items():
        #print k,':',v,'***********'
        return iData

