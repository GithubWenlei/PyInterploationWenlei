
# -*- coding: utf-8 -*-
"""
Created on 2020/10/02 By 文磊
contact=wenlei6037@hhu.edu.cn
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
# import Functions as fc
import os
import pandas as pd
import numpy as np
import datetime
import timeit
from pyIdw import pyIdw
from readData import ReadData
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

rd=ReadData(deltaTimeMin)
cols,rows,xmin,ymin,cellsize,NODATA_value,dem=rd.readASCIIGrid(demfile)#读取dem数据
gages_xyz,czbm=rd.readgagexyz(gagesfile=gagefile)
stop=timeit.default_timer()
print("读取数据用时%.2f 秒"%(stop-start))
nstation=gages_xyz.shape[0]
start_time = datetime.datetime.strptime(startTime1, '%Y-%m-%d %H:%M:%S')
end_time = datetime.datetime.strptime(endTime1, '%Y-%m-%d %H:%M:%S')
ntimes=rd.ntimes(start_time,end_time,deltaTimeMin)
outHourP=np.zeros((ntimes,nstation))
ig=0
os.system("dir /s /b *00.xlsx >file.txt") #获取当前路径下所有后缀名为xlsx的文件路径
f=open('file.txt','r').readlines()
writer=pd.ExcelWriter(filename)
for ifname in f:
    writer=rd.run(ifname[:-1], start_time,  end_time, writer)
    outHourP[:,ig]=rd.outHourPtemp
    ig+=1
    stopp = timeit.default_timer()
    print("完成了第%i 站点时间序列降水插值，插值了%i 分钟，共用时 %.2f 秒" % (ig, len(rd.outP),stopp - stop))
writer.save()
stop1=timeit.default_timer()
print("插值时间序列降水用时 %.2f 秒"%(stop1-stop))
if IsReadPrecip:
    rfintensity=rd.readgagerainfall(filename,start_time, end_time,nstation,czbm)#读取插值好的降雨数据
idw=pyIdw(gages_xyz,dem,outHourP,xmin,ymin,cellsize,start_time, end_time,isplotline=False)#反距离插值方法的权重系数
outData=idw.outData
stop2=timeit.default_timer()
print("网格插值了%i 个时段，用时 %.2f 秒"%(ntimes,stop2-stop1))
if Saverts:
    P=np.array(outData,dtype=np.float32)
    P.tofile('Siqian199207.rts')
stop3=timeit.default_timer()
print("存rts文件 %.2f 秒"%(stop3-stop2))
stop4=timeit.default_timer()
if isCreatGif:
    gif_name="PidwSiqian1.gif"
    path="out_pic"
    idw.creat_gif(gif_name,path,duration=0.1)
print("总用时 %.2f 秒"%(stop4-start))
idw.plotgrid(itime=13)
# idw.plotline(deltaTimeMin)