
# -*- coding: utf-8 -*-
"""
Created on 2020/10/02 By 文磊
功能：1、将不等时间间隔的雨量站降水插值为等时间间隔的降水数据，其中时间间隔可是用户指定；
     并将结果存入filename excel文件中。
     2、选取开始和结束时间，并将该时间段内的降雨数据采用反距离插值方法插值到网格上；并将
     结果存为nc文件或者rts的二进制文件。
     3、画图显示反距离插值后的各时段的网格降水量，以及流域平面面降水量的过程线。
     4、将插值的网格降水输出为gif动态图。
filename 输出时间序列插值后降雨文件名
startTime1 空间反距离插值的开始时间
endTime1 空间反距离插值的结束时间
deltaTimeMin=60 降雨插值时间间隔，单位分钟
demfile 插值网格的DEM文件名
gagefile 雨量站文件名
gagefile中文件内容如下例子所示
czbm	x	y	z
71020100	5.57E+05	3.08E+06	5.87E+02
71020200	5.54E+05	3.09E+06	6.80E+02
71020300	5.52E+05	3.09E+06	6.54E+02
71020400	5.51E+05	3.09E+06	3.95E+02
power 反距离插值的指数
ifIDWZ 反距离插值的距离是考虑高程，是=True；否=False
maxdistance 反距离插值的最大影响距离
ifPlot 是否绘图；是=True;否=False
SaveNc 是否将结果存为NC文件；是=True;否=False
Saverts 是否将结果存为rts二进制文件；是=True;否=False
isCreatGif 是否创建Gif动态图；是=True;否=False
IsReadPrecip 是否读取已经插值好的降水数据；是=True;否=False
Note:
原始被插值的各站点的时间序列excel文件中的格式如下四列内容，分别为测站编码，开始时间，结束时间，降水量
STCD	BGTM	ENDTM	P
71020100	1970/5/1 18:00	1970/5/1 19:00	3.1
71020100	1970/5/1 19:00	1970/5/1 20:00	1.9
@author: wenlei
====================================================================================================
"""
import Functions as fc
import os
import pandas as pd
import numpy as np
import datetime
import timeit
start=timeit.default_timer()
print(__doc__)
deltaTimeMin=60
filename="outrain_%i_Min.xlsx"%deltaTimeMin
startTime1='1992-07-03 08:00:00'
endTime1='1992-07-07 16:00:00'
demfile="demsqian.txt"
gagefile="gages1.xlsx"
power=2
ifIDWZ=True
maxdistance=100000
ifPlot=False
SaveNc=True
Saverts=True
isCreatGif=False
IsReadPrecip=False
cols,rows,xmin,ymin,cellsize,NODATA_value,dem=fc.readASCIIGrid(demfile)#读取dem数据

gages_xyz,czbm=fc.readgagexyz(gagesfile=gagefile)
stop=timeit.default_timer()
print("读取数据用时%.2f 秒"%(stop-start))
nstation=gages_xyz.shape[0]

start_time = datetime.datetime.strptime(startTime1, '%Y-%m-%d %H:%M:%S')
end_time = datetime.datetime.strptime(endTime1, '%Y-%m-%d %H:%M:%S')

ntimes = int((end_time - start_time).total_seconds() / 60/deltaTimeMin)+1
outData=np.zeros((ntimes,rows,cols))
outHourP=np.zeros((ntimes,nstation))
ig=0
os.system("dir /s /b *00.xlsx >file.txt") #获取当前路径下所有后缀名为xlsx的文件路径
f=open('file.txt','r').readlines()
writer=pd.ExcelWriter(filename)
for ifname in f:
    stcd,startTime, endTime, p = fc.readexcel(ifname[:-1])
    outTime, outp=fc.interpolation(startTime, endTime, p, deltaTimeMin=deltaTimeMin)#deltaTimeMin为插值的时间间隔
    starti=int((start_time-outTime[0]).total_seconds()/60/deltaTimeMin)
    outHourP[:,ig]=outp[starti:starti+ntimes]
    ig+=1
    out_excel = pd.DataFrame()
    out_excel['Time'] = pd.Series(outTime)
    out_excel['P'] = pd.Series(outp)
    stopp = timeit.default_timer()
    out_excel.to_excel(writer,sheet_name=str(int(stcd)), header=True, index=False)#该行代码用时最多
    stopp = timeit.default_timer()
    print("完成了第%i 站点时间序列降水插值，插值了%i个时段，共用时 %.2f 秒" % (ig, len(outp),stopp - stop))
writer.save()
stop1=timeit.default_timer()
print("插值时间序列降水用时 %.2f 秒"%(stop1-stop))
if IsReadPrecip:
    rfintensity=fc.readgagerainfall(filename,startTime1, endTime1,nstation,czbm)#读取插值好的降雨数据
outData=fc.idw(gages_xyz,dem,xmin,ymin,cellsize,outHourP,power=power,ifZ=ifIDWZ,maxdistance=maxdistance)#反距离插值方法的权重系数
stop2=timeit.default_timer()
print("网格插值了%i 个时段，用时 %.2f 秒"%(ntimes,stop2-stop1))
if SaveNc:
    fc.writeNc(dem, outData, xmin, ymin, cellsize, startTime1, endTime1,file_name='outIDWP.nc')#将结果写入nc文件
if Saverts:
    P=np.array(outData,dtype=np.float32)
    P.tofile('Siqian199207.rts')
stop3=timeit.default_timer()
print("存nc文件 %.2f 秒"%(stop3-stop2))
if ifPlot:
    for i in range(ntimes):
        fc.plotgrid(outData,itime=i)
    fc.plotline(outData)
stop4=timeit.default_timer()
print("画图 %.2f 秒"%(stop4-stop3))
if isCreatGif:
    gif_name="PidwSiqian.gif"
    path="out_pic"
    fc.creat_gif(gif_name,path,duration=0.1)
fc.plotline(outData)
print("总用时 %.2f 秒"%(stop4-start))