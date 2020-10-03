# -*- coding: utf-8 -*-
"""
Created on 2020/10/02 By 文磊
contact=wenlei6037@hhu.edu.cn
author wenlei
"""
import pandas as pd
import numpy as np
from datetime import timedelta
class ReadData():
    def __init__(self,deltaTimeMin):
        print("functions: readexcel,readASCIIGrid,readgagexyz,readgagerainfall,readNC")
        self.deltaTimeMin=deltaTimeMin
    def readexcel(self,filename):
        """
        该函数的目的是从excel文件中读取降水数据
        :return:
        """
        xls = pd.ExcelFile(filename)
        table1 = xls.parse(0)  # xls.parse("Sheet1")
        # print(table1.keys())
        stcd = table1["STCD"][0]
        self.startTime = table1["BGTM"]
        self.endTime = table1["ENDTM"]
        self.p = table1["P"]
        return stcd
    def ntimes(selfself,start_time,end_time,deltaTimeMin):
        return int((end_time - start_time).total_seconds() / 60/deltaTimeMin)+1
    def readASCIIGrid(self,rastername, head=True):
        """
        读取Arcgis导出的ASCII格式栅格数据
        :param rastername:
        :param head:
        :return:
        """
        if head:
            demio = open(rastername, 'r')
            dem = demio.readlines()
            demio.close()
            try:
                cols = int(dem[0][5:])
                rows = int(dem[1][5:])
                xllcorner = float(dem[2][9:])
                yllcorner = float(dem[3][9:])
                cellsize = float(dem[4][8:])
                NODATA_value = int(dem[5][12:])
                raster = np.loadtxt(rastername, skiprows=6)
            except Exception as e:
                # print('First line is headers for %s file'%rastername)
                print(e)
                cols = int(dem[1][5:])
                rows = int(dem[2][5:])
                xllcorner = float(dem[3][9:])
                yllcorner = float(dem[4][9:])
                cellsize = int(dem[5][8:])
                NODATA_value = int(dem[6][12:])
                raster = np.loadtxt(rastername, skiprows=7)
            return cols, rows, xllcorner, yllcorner, cellsize, NODATA_value, raster
        else:
            cols, rows, xllcorner, yllcorner, cellsize, NODATA_value = 1, 1, 0, 0, 0, 0
            raster = np.loadtxt(rastername)
        return cols, rows, xllcorner, yllcorner, cellsize, NODATA_value, raster

    def readgagexyz(self,gagesfile='gages.xlsx'):
        """
        :param filename: file name of rainfall excel file
        :param starttime: start time of rainfall
        :param endtime: end time of rainfall
        :param gagesfile: file name of rainfall gages
        :return: gages_xyz: x y,z of precipitation station [nstation,3]
                 czbm: code of station
        """
        gf = pd.read_excel(gagesfile, sheet_name='Sheet1')
        self.czbm = gf['czbm']
        rgx = gf['x']
        rgy = gf['y']
        rgz = gf['z']
        self.gages_xyz = np.array((rgx, rgy, rgz)).T  # gages_xyz[nstations,3]
        return self.gages_xyz, self.czbm

    def readgagerainfall(self,filename, start_time, end_time, nrg, czbm):
        """
        :param filename: file name of rainfall excel file
        :param starttime: start time of rainfall
        :param endtime: end time of rainfall
        :param nrg: number of rainfall gages
        :param czbm: code of rainfall gages
        :return: rfintensity:precipitation data  [ntimes,nstation],
        """
        npair = int((end_time - start_time).total_seconds() / 60/self.deltaTimeMin) + 1  # n hours
        rfintensity = np.zeros((npair, nrg), dtype=np.float)
        irg = 0
        for sheetname in czbm:
            print(sheetname)
            tabler = pd.read_excel(filename, sheet_name=str(int(sheetname)))
            timer = tabler[u"Time"]
            rainfall = tabler[u'P(mm)']
            deltatime = start_time - timer[0]
            startrow = int(deltatime.total_seconds() / 3600)
            rfintensity[:, irg] = rainfall[startrow:startrow + npair]
            irg += 1
        return rfintensity

    def deltaMin(self,startT,endT):
        return np.int((startT - endT).total_seconds() / 60)
    def interpolation(self):
        """
        :param startTime: 降水量的开始时间序列
        :param endTime: 降水量的结束时间序列
        :param p: 时段累积降水量
        :param deltaTimeMin: 输出的降水时间间隔
        :return: outTime,outP 分别为输出的时间与对应的降水量
        """
        totalMin = self.deltaMin(self.endTime[len(self.endTime)-1] , self.startTime[0])
        pMin = np.zeros(int(totalMin))
        for i in range(len(self.startTime)):
            j = self.deltaMin(self.startTime[i], self.startTime[0])
            n = self.deltaMin(self.endTime[i],self.startTime[i])
            pi = self.p[i] / n
            pMin[j:j + n] = pi
        outN = int(totalMin / self.deltaTimeMin)
        m = self.startTime[0].minute
        if m == 0:
            outStartTime = self.startTime[0]
            outEndTime = outStartTime + timedelta(minutes=self.deltaTimeMin * outN)
        else:
            outStartTime = self.startTime[0] + timedelta(minutes=(-m))
            outEndTime = outStartTime + timedelta(minutes=self.deltaTimeMin * outN)
        self.outTime = pd.date_range(outStartTime, outEndTime, periods=outN + 1)
        self.outP = np.zeros(len(self.outTime))
        starti = self.deltaMin(outStartTime,self.startTime[0])
        if starti > 0:
            self.outP[0] = np.sum(pMin[:starti])
        for i in range(1, len(self.outTime)):
            if starti + (i - 1) * self.deltaTimeMin >= 0:
                self.outP[i] = np.sum(pMin[starti + (i - 1) * self.deltaTimeMin:starti + i * self.deltaTimeMin])
    def run(self,filename,start_time, end_time,writer):
        ntimes=self.ntimes(start_time,end_time,self.deltaTimeMin)
        stcd = self.readexcel(filename)
        self.interpolation()  # deltaTimeMin为插值的时间间隔
        starti = self.ntimes(self.outTime[0], start_time, self.deltaTimeMin) - 1
        self.outHourPtemp = self.outP[starti:starti + ntimes]
        out_excel = pd.DataFrame()
        out_excel['Time'] = pd.Series(self.outTime)
        out_excel['P(mm)'] = pd.Series(self.outP)
        out_excel.to_excel(writer, sheet_name=str(int(stcd)), header=True, index=False)  # 该行代码用时最多
        return writer
    def readNC(self,ncfile):
        from netCDF4 import Dataset
        nc_obj = Dataset(ncfile)
        # 查看nc文件有些啥东东
        print(nc_obj)
        print('---------------------------------------')
        # 查看nc文件中的变量
        print(nc_obj.variables.keys())
        for i in nc_obj.variables.keys():
            print(i)
        print('---------------------------------------')
        # 查看每个变量的信息
        print(nc_obj.variables['time'])
        print(nc_obj.variables['X'])
        print(nc_obj.variables['Y'])
        print(nc_obj.variables['p'])