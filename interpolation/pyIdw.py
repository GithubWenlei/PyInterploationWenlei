# -*- coding: utf-8 -*-
"""
Created on 2020/10/02 By 文磊
contact=wenlei6037@hhu.edu.cn
author wenlei
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
class pyIdw():
    def __init__(self,station_xyz,DEM,outHourP,xmin,ymin,cellsize,startTime,
                 endTime,ifZ=True,power=2,maxdistance=100000,
                 ifPlotgrid=False,SaveNc=True,isplotline=True):
        self.ifZ=ifZ
        self.power=power
        self.maxdistance=maxdistance
        self.DEM=DEM
        self.station_xyz=station_xyz
        self.outHourP=outHourP
        self.nstation = station_xyz.shape[0]
        self.nrows = DEM.shape[0]
        self.ncols = DEM.shape[1]
        self.ntimes = outHourP.shape[0]
        self.a = np.zeros((self.nstation, self.nrows, self.ncols))
        self.lats = np.linspace(ymin + cellsize * (self.nrows - 1), ymin, self.nrows)
        self.lons = np.linspace(xmin, xmin + cellsize * (self.ncols - 1), self.ncols)
        self.xy = np.meshgrid(self.lons, self.lats)
        self.X = self.xy[0]
        self.Y = self.xy[1]
        self.d = np.zeros((self.nstation, self.nrows, self.ncols))
        self.startTime = startTime
        self.endTime = endTime
        self.date_range = pd.date_range(self.startTime, self.endTime, periods=self.ntimes)
        self.runidw()
        self.isPlotgrid=ifPlotgrid
        self.SaveNc=SaveNc
        self.isplotline=isplotline
        if self.isPlotgrid:
            for i in range(self.ntimes):
                print("ifPlotgrid is True")
                print("Now is plotting the %i grid picture..."%(i+1))
                self.plotgrid(self,itime=i)
        if self.SaveNc:
            print("SaveNc is True")
            self.writeNc()
        if self.isplotline:
            print("isplotline is True")
            self.plotline()

    def runidw(self):
        for k in range(self.nstation):
            if self.ifZ:
                self.d[k, :, :] = np.sqrt(np.power(self.X - self.station_xyz[k, 0], 2) + np.power(self.Y - self.station_xyz[k, 1], 2) + np.power(
                    self.DEM - self.station_xyz[k, 2], 2))
            else:
                self.d[k, :, :] = np.sqrt(np.power(self.X - self.station_xyz[k, 0], 2) + np.power(self.Y - self.station_xyz[k, 1], 2))
            self.a[k, :, :] = 1.0 / np.power(self.d[k, :, :], self.power)
            self.a[k, :, :][self.d[k, :, :] > self.maxdistance] = 0
        sumidw = np.sum(self.a, axis=0)
        sumidw[sumidw == 0] = 1
        self.a = self.a / sumidw
        ab = self.a.reshape(self.nstation, self.nrows * self.ncols)  # 转为2为矩阵
        bb = np.dot(self.outHourP, ab)  # 降水和权重系数的矩阵相乘
        self.outData = bb.reshape((self.ntimes,self.nrows, self.ncols))  #
        return self.outData

    def plotgrid(self, itime=0):
        """
        绘制网格图
        :return:
        """
        import seaborn as sns
        import os
        fig, ax = plt.subplots()
        fig.suptitle("IDW precpitation at Time %i h" % (itime + 1))
        ax = sns.heatmap(self.outData[itime, :, :], cmap='jet', square=True)
        # plt.show()
        if not (os.path.exists('out_grid_pic')):  os.mkdir('out_grid_pic')
        fig.savefig("out_grid_pic/IDW_precpitation_at_Time_%i_h.png" % (itime + 1))
        plt.close()
    def plotline(self,deltaTimeMin, savetxt=True):
        # import seaborn as sns
        meanp = []
        for i in range(self.outData.shape[0]):
            meanp.append(np.mean(self.outData[i, :, :]))
        fig, ax = plt.subplots(figsize=(10, 7))
        x=np.arange(len(meanp))+1
        x=x*deltaTimeMin/60
        ax.plot(x,meanp, 'r')
        ax.set_xlabel("Time(h)")
        ax.set_ylabel("basin mean precip($mm$)")
        plt.show()
        fig.savefig("meanprecip_%i_min.png"%deltaTimeMin)
        plt.close()
        if savetxt:
            np.savetxt("meanprecip_%i_min.txt"%deltaTimeMin, meanp, fmt="%.2f")
    def creat_gif(self,gif_name, path, duration=0.3):
        '''
        生成gif文件，原始图片仅支持png格式
        gif_name ： 字符串，所生成的 gif 文件名，带 .gif 后缀
        path :      需要合成为 gif 的图片所在路径
        duration :  gif 图像时间间隔
        '''
        import imageio
        frames = []
        pngFiles = os.listdir(path)
        inpng = []
        for i in range(len(pngFiles)):
            inpng.append("IDW_precpitation_at_Time_%i_h.png" % (i + 1))
        image_list = [os.path.join(path, f) for f in inpng]
        for image_name in image_list:
            frames.append(imageio.imread(image_name))
        imageio.mimsave(gif_name, frames, 'GIF', duration=duration)

    def writeNc(self, file_name='outIDWP.nc'):
        """
        environment: netCDF4,pandas,numpy
        startTime, start time of precp data,format('%Y-%m-%d %H:%M:%S')
        endTime, end time of precp data,format('%Y-%m-%d %H:%M:%S')
        """
        import netCDF4 as nc
        if os.path.exists(file_name):
            os.remove(file_name)
        da = nc.Dataset(file_name, 'w', format="NETCDF4")
        da.createDimension('latitude', self.nrows)
        da.createDimension('longitude', self.ncols)
        da.createDimension('time', size=None)
        X = da.createVariable("X", 'f', ("longitude"))
        Y = da.createVariable("Y", 'f', ("latitude"))
        time = da.createVariable("time", 'S19', dimensions='time')
        X.units = 'meters east'
        Y.units = 'meters north'
        da.variables['Y'][:] = self.lats
        da.variables['X'][:] = self.lons
        da.times = time.shape[0]
        for itime in range(self.ntimes):
            time[itime] = self.date_range[itime].strftime('%Y-%m-%d %H:%M:%S')
        time.units = 'times since {0:s}'.format(time[0])
        da.createVariable('p', 'f8', ('time', 'latitude', 'longitude'))
        da.variables['p'][:] = self.outData
        da.close()