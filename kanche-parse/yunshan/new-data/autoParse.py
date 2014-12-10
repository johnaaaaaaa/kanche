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
        self.gatherDate = pData['create_at']        
        self.html = pData['details']
        self.hxs = Selector(text=self.html, type="html")
        self.summary = pData['summary']
        self.shxs = Selector(text=pData['summary'], type="html")



        iTmp = self.hxs.xpath(u'//*[text()="??" or contains(text(),"??")]')
        if len(iTmp):
            self.summaryBox = self.getSummaryBox(iTmp[0])
        else:
            self.summaryBox = self.hxs.xpath('/html/body')
    
    #????
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
            
    #???????
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
            
    #????xpath
    def getXpath(self,pNode,pList):
        rNode = pNode.xpath('./..')[0]
        tagName = self.getTagName(rNode)
        if tagName[0] in ['','body']:
            return u'//%s'%('/'.join(pList))
        else:
            pList.insert(0,''.join(tagName))
            return self.getXpath(pNode.xpath('./..'),pList)
            
    #??????
    def getSummaryBox(self, pNode):
        iNode = pNode.xpath('./..')[0]
        if u'???' in iNode.extract() and len(iNode.xpath('.//img')):
            return iNode
        else:
            return self.getSummaryBox(iNode)
        
    # ????
    def parseDate(self, pTxt, pDate):
        iTxt = pTxt
        iResult = ''
        if iTxt.find(u'?') > -1:
            iTmp = int(re.findall('(\d+)', iTxt)[0])
            if iTxt.find(u'?') > -1:
                iInterval = timedelta(seconds=iTmp)
            elif iTxt.find(u'??') > -1:
                iInterval = timedelta(minutes=iTmp)
            elif iTxt.find(u'??') > -1:
                iInterval = timedelta(hours=iTmp)
            elif iTxt.find(u'?') > -1:
                iInterval = timedelta(days=iTmp)
            elif iTxt.find(u'?') > -1:
                iInterval = timedelta(days=iTmp * 30)
            elif iTxt.find(u'??') > -1:
                iInterval = timedelta(weeks=iTmp)
            elif iTxt.find(u'?') > -1:
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


    # ?????
    def getUrl(self):
        iResult = self.data['url'].split('#')[0].split('?')[0]
        return iResult


    #??ID
    def getPageId(self):
        iResult = ''
        iNodeList = self.data['url'].split('.')[-2].split('/')[-1]
        iTmp = re.findall('\d+', iNodeList)
        if len(iTmp):
            iResult = iTmp[0]
        return iResult


    #??
    def getTitle(self):
        iResult = ''
        iNodeList = self.hxs.xpath('//h1 | //h2 | //h3')
        for iItem in iNodeList:
            iTxt = ' '.join(iItem.xpath('text()').extract()).strip()
            iTxt = iTxt.strip()
            if len(re.findall(u'(\d{2,4})?', iTxt)):

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


    #??ID
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


    #??ID
    def getDealerId(self):
        iResult = '0'
        try:
            iNodeList = self.hxs.xpath(u'//a[contains(text(),"??") and contains(text(),"?")]/@href').extract()
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


    #??????

    def getPubDate(self):
        iResult = ''
        try:
            # flag = True
            # if u'51auto.com' == self.data['site']:
            #
            # if 'pubDate' in self.data.keys():
            #     iTxt = self.data['pubDate'].strip()
            #     if len(iTxt):
            #         iResult = self.parseDate(iTxt, self.gatherDate)
            #         flag = False
            #
            # if flag:

            iNodeList = self.hxs.xpath(u'//*[contains(text(),"??") or contains(text(),"??")]/text()').extract()
            for iTxt in iNodeList:
                if len(re.findall('\d+', iTxt)):
                    iTxt = iTxt.replace(u'??', '').replace(u'??', '').strip()
                    iResult = self.parseDate(iTxt, self.gatherDate)
                    if iResult != '': break

            if iResult == '':
                iNodeList = self.shxs.xpath('//*/text()').extract()
                for i in xrange(len(iNodeList)-1,-1,-1):
                    iTxt = iNodeList[i]
                    if len(re.findall('\d+', iTxt)) and (iTxt.find(u'?') or len(re.findall('\d{4}', iTxt))):
                        iResult = self.parseDate(iTxt, self.gatherDate)
                        if iResult != '':break

        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult


    #??
    def getPrice(self):
        iResult = ''
        try:
            iTitle = self.getTitle()
            iNodeList = self.hxs.xpath(u'//body//*[contains(*,"?")]')
            for iItem in iNodeList:
                #print iItem.extract(),'&&&&&'
                iSubList = iItem.xpath('..//*/text() | ../..//*/text()').extract()
                for iSub in iSubList:
                    if iSub != '' and iSub.find(u'??') == -1:
                        iSub = iSub.replace(u'¥', '').replace(u'?', '').strip()
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


    #???
    def getMileage(self):
        iResult = 0
        try:
            iNodeList = self.hxs.xpath(u'//*[contains(text(),"???")]')

            for iItem in iNodeList:
                iTmp = ' '.join(iItem.xpath(u'../*/text()').extract()).strip()
                iTmp = re.findall(u':?(\d+\.\d+)???', iTmp)
                if len(iTmp):
                    iResult = int(float(iTmp[0]) * 10000)
            return iResult
        except:
            iResult = 0

    #????
    def getFirstRegistrationDate(self):
        iResult = ''

        iNodeList = self.hxs.xpath(u'//text()[contains(.,"??")]/../..')
        for iItem in iNodeList:
            iTmp = iItem.xpath('text() | */text()').extract()
            iTxt = ''.join(iTmp).strip()
            iTmp = re.findall(u'(\d{4}?\d{1,2}?)', iTxt)
            if len(iTmp):
                iResult = iTmp[0].replace(u'?', '-').replace(u'?', '-') + '01'
                break
	    else:
		iTmp = re.findall(u'(\d{4}?)', iTxt)
		if len(iTmp):
                    iResult = iTmp[0].replace(u'?', '-') + '01-' + '01'
                    break


        return iResult


    #????
    def getCarUsage(self):
        iResult = ''

        iNodeList = self.hxs.xpath(u'//text()[contains(.,"?") and contains(.,"?")]/../..')
        for iItem in iNodeList:
            iTmp = iItem.xpath('text() | */text()').extract()

            iTxt = re.sub(u'?[ \s ]*?', u'??', '\n'.join(iTmp).strip())
            if iTxt.find(u'??') > -1:
                iTxt = re.split(u'??\s*[::]?\s*', iTxt)[1].split('\n')[0]
                iResult = iTxt
                break

        if iResult == '':
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"????")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = '\n'.join(iTmp).strip()
                iTxt = re.split(u'??\s*[::]?\s*', iTxt)[1].split('\n')[0]
                iResult = iTxt
                break
        return iResult


    #????

    def getExteriorColor(self):
        iResult = ''
        self.color=''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"?") and contains(.,"?") or contains(.,"??")]/../..')
            if iNodeList:
                for iItem in iNodeList:
                    iTmp = iItem.xpath('text() | */text()').extract()
                    iTxt = ' '.join(iTmp).strip()
                    color = re.compile(u'?[::]?\s*([\u4e00-\u9fa5\-]+)').findall(iTxt)
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


    #????
    def getInteriorColor(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"??") and contains(.,"?") and contains(.,"?")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=' '.join(iTmp).strip()
                if iTxt:
                    if iTxt.find(u"?") >= 0:
                        iResult = "deep"
                        break
                    elif iTxt.find(u"?") >= 0:
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

    #??
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
                iTmp = re.split(u',|,',','.join(iTmp))
                iDict = {}
                for i in iTmp:
                    if (u'???' in i or u'??' in i) and i.find(u'??')>1:
                        iTxt = i.split(u'??')[0]
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
    
    #????
    def getAddress(self):
        iResult = ''
        
        iLst = []
        iNodeList = self.summaryBox.xpath(u'.//*[contains(text(),"???") or contains(@class,"dress") or contains(@id,"dress")]/..')
        for iTmp in iNodeList:
            for iItem in iTmp.xpath('text()|.//text()'):
                iTxt = iItem.extract().strip()
                iTxt = re.sub(u'?[^?]+?','',iTxt).replace(u'???','')
                if re.sub('[\d \-]','',iTxt)!='' and len(iTxt)>4:
                    iLst.append(iTxt)
            
        iResult = '\n'.join(iLst)
        return iResult
        
    #????
    def getEmissionStandard(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"????")]/../.. | @title[contains(.,"????")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                #iResult = iTmp
                for i, element in enumerate(iTmp):
                    if element.find(u"?") >= 0 or element.find(u"?") >= 0 or element.find(u"?") >= 0:
                        if element.find(u':') >= 0:
                            iResult = element.split(':')[1]
                        else:
                            iResult = element
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult


    #??
    def getWarrantyDate(self):
        iResult = ''
        try:

            

            iNodeList = self.hxs.xpath(u'//text()[contains(.,"??")]/../..')


            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = ''.join(iTmp).strip()
                zhibao=re.findall(u'??[^\d]*(\d{4})[^\d](\d{1,2})',iTxt)
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
    #???


    def getCompulsoryInsurance(self):
        iResult = ''
        try:

            iNodeList = self.hxs.xpath(u'//text()[contains(.,"???") or contains(.,"??")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=''.join(iTmp).strip()
                baoxian=re.findall(u'???[^\d]*(\d{4})[^\d](\d{1,2})|???[^\d]*(\d{4})[^\d](\d{1,2})',iTxt)

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


    #???
    def getBusinessInsExpDate(self):
        iResult = ''
        try:

            iNodeList = self.hxs.xpath(u'//text()[contains(.,"???")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = ' '.join(iTmp).strip()
                business=re.findall(u'???[^\d]*(\d{4})[^\d]*(\d{1,2})',iTxt)
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


    #??
    def getInspectionOfValidity(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"??") or contains(.,"??")]/../..')

            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = ' '.join(iTmp).strip()
                #print iTxt,'^^^^^^^^^^^^^^^'
                nianjian=re.findall(u'?[^\d]*(\d{4})[^\d]*(\d{1,2})',iTxt)
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


    #???
    def getVehicleAndVesselTax(self):
        iResult = ''
        try:

            iNodeList = self.hxs.xpath(u'//text()[contains(.,"??") and contains(.,"?")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt = ' '.join(iTmp).strip()
                #print iTxt,'^^^^^^^^^^^^^^^'

                chechuan=re.findall(u'??[^\d]*(\d{4})',iTxt)
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


    #???
    def getRegistration(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"???")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=''.join(iTmp).strip()
                #print iTxt,'&&&&&&&&&&&&&&&&&&'
                iTvl=re.findall(u'???[^\w]*([\u4e00-\u9fa5\-]+)',iTxt)
                #print iTvl[0],'*******************'
                if iTvl:
                    if u'?'in iTvl[0]:
                        iResult=True
                        break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        return iResult


    #???
    def getDrivingLicense(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"???")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=''.join(iTmp).strip()
                #print iTxt,'&&&&&&&&&&&&&&&&&&'
                iTvl=re.findall(u'???[^\w]*([\u4e00-\u9fa5\-]+)',iTxt)
                #print iTvl[0],'*******************'
                if iTvl:
                    if u'?'in iTvl[0]:
                        iResult=True
                        break


        except Exception as e:
                    print e
                    print "======================"
                    traceback.print_exc(file=sys.stdout)
                    print "======================"

                    iResult = ''
        return iResult


    #????
    def getVehiclePurchaseInvoice(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"????")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                iTxt=''.join(iTmp).strip()
                #print iTxt,'&&&&&&&&&&&&&&&&&&'
                iTvl=re.findall(u'????[^\w]*([\u4e00-\u9fa5\-]+)',iTxt)
                #print iTvl[0],'*******************'
                if iTvl:
                    if u'?'in iTvl[0]:
                        iResult=True
                        break

        except Exception as e:
                print e
                print "======================"
                traceback.print_exc(file=sys.stdout)
                print "======================"

                iResult = ''
        return iResult


    #????
    def getTransferTimes(self):
        iResult = 0
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"????")]/../..')

            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | *//text()').extract()
                iTxt=''.join(iTmp).strip()
                #print iTxt,'***************'
                iTvl=re.findall(u'??[^\d]*(\d{1,2})',iTxt)
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


    #????
    def getImageURL(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(
                u'//text()[contains(.,"??")]/../../../../following-sibling::* | //text()[contains(.,"????")]/../../../../following-sibling::*')

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


    #????
    def getSellerName(self):
        iResult = ''
        #contains(text(),"linkman")
        iNodeList = self.hxs.xpath(u'.//*[(contains(text(),"?") and contains(text(),"?") and contains(text(),"?")) and not(contains(text(),"????"))]')
        if len(iNodeList):
            iTxt = iNodeList[0].xpath('text()').extract()[0]
            if len(iTxt.replace(u'?','').replace(u'?','').replace(u'?','').replace(u':','').strip())<2:
                iTmp = iNodeList[0].xpath('./../text()|./..//*/text()').extract()
                iTxt = iTmp[-2] if iTmp[-1].strip()=='' else iTmp[-1]
                iResult = iTxt
            else:
                iTxt = re.sub(u'[?:]','',re.split(u'[ ?]',iTxt.split(u'???')[1])[0])
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

    #????-??
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


    #????-??
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


    #????


    def getComments(self):
        iResult = ''
        return iResult
        try:
            iNodeList = self.hxs.xpath(
                u'//text()[contains(.,"??")]/../../../../following-sibling::* | //text()[contains(., "????")]/../../../../following-sibling::* | //text()[contains(.,"??")]/../../../.ollowing-sibling::*[position()=1] ')

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


    #????
    def getMaintainceRecords(self):
        iResult = ''
        try:
            iNodeList = self.hxs.xpath(u'//text()[contains(.,"??")]/../..')
            for iItem in iNodeList:
                iTmp = iItem.xpath('text() | */text()').extract()
                if iTmp[0].find(u"??") >= 0 and len(iTmp) > 1:
                    iResult = iTmp[1]
        except Exception as e:
            print e
            print "======================"
            traceback.print_exc(file=sys.stdout)
            print "======================"

            iResult = ''
        return iResult


    #????
    def getGatherDate(self):
        iResult = self.data['create_at']
        return iResult


    #??ID

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

