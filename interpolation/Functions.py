__author__ = 'Wenlei'
"""
2020/10/02
"""
import pandas as pd
import numpy as np
import datetime
def readexcel(filename):
    """
    该函数的目的是从excel文件中读取降水数据
    :return:
    """
    xls=pd.ExcelFile(filename)
    table1=xls.parse(0)# xls.parse("Sheet1")
    stcd=table1["STCD"][0]
    startTime=table1["BGTM"]
    endTime=table1["ENDTM"]
    p=table1["P"]
    return stcd,startTime,endTime,p
def interpolation(startTime,endTime,p,deltaTimeMin=60):
    """
    :param startTime: 降水量的开始时间序列
    :param endTime: 降水量的结束时间序列
    :param p: 时段累积降水量
    :param deltaTimeMin: 输出的降水时间间隔
    :return: outTime,outP 分别为输出的时间与对应的降水量
    """
    totalMin=np.int((endTime[len(endTime)-1]-startTime[0]).total_seconds()/60)
    pMin=np.zeros(int(totalMin))
    for i in range(len(startTime)):
        j=np.int((startTime[i] - startTime[0]).total_seconds() / 60)
        n=np.int((endTime[i] - startTime[i]).total_seconds() / 60)
        pi=p[i]/n
        pMin[j:j+n]=pi
    outN=int(totalMin/deltaTimeMin)
    m=startTime[0].minute
    if  m== 0:
        outStartTime = startTime[0]
        outEndTime = outStartTime + datetime.timedelta(minutes=deltaTimeMin*outN)
    else:
        outStartTime=startTime[0]+datetime.timedelta(minutes=(-m))
        outEndTime=outStartTime + datetime.timedelta(minutes=deltaTimeMin*outN)
    outTime = pd.date_range(outStartTime, outEndTime, periods=outN+1)
    outP=np.zeros(len(outTime))
    starti=int((outStartTime-startTime[0]).total_seconds()/60)
    if starti>0:
        outP[0]=np.sum(pMin[:starti])
    for i in range(1,len(outTime)):
        if starti+(i-1)*deltaTimeMin >= 0:
            outP[i]=np.sum(pMin[starti+(i-1)*deltaTimeMin:starti+i*deltaTimeMin])
    return outTime, outP
def readASCIIGrid(rastername,head=True):
    """
    读取Arcgis导出的ASCII格式栅格数据
    :param rastername:
    :param head:
    :return:
    """
    if head:
        demio=open(rastername,'r')
        dem=demio.readlines()
        demio.close()
        try:
            cols=int(dem[0][5:])
            rows=int(dem[1][5:])
            xllcorner=float(dem[2][9:])
            yllcorner=float(dem[3][9:])
            cellsize=float(dem[4][8:])
            NODATA_value=int(dem[5][12:])
            raster = np.loadtxt(rastername, skiprows=6)
        except Exception as e:
            #print('First line is headers for %s file'%rastername)
            print(e)
            cols=int(dem[1][5:])
            rows=int(dem[2][5:])
            xllcorner=float(dem[3][9:])
            yllcorner=float(dem[4][9:])
            cellsize=int(dem[5][8:])
            NODATA_value=int(dem[6][12:])
            raster=np.loadtxt(rastername,skiprows=7)
        return cols,rows,xllcorner,yllcorner,cellsize,NODATA_value,raster
    else:
        cols, rows, xllcorner, yllcorner, cellsize, NODATA_value=1,1,0,0,0,0
        raster=np.loadtxt(rastername)
    return cols,rows,xllcorner,yllcorner,cellsize,NODATA_value,raster
# def distance()
def idw(station_xyz,DEM,xmin,ymin,cellsize,outHourP,power=2,ifZ=False,maxdistance=100000):
    """
    :param station_xyz: 雨量站的x,y,z坐标，维度：[nstations,3];float; meter
    :param DEM: 网格高程数据，纬度：[nrows,ncols]
    :param xmin: 网格x最小值，即DEM最左下角网格的x值；float;meter
    :param ymin: 网格y最小值，即DEM最左下角网格的y值；float;meter
    :param cellsize: 网格大小；meter
    :param power: 反距离权重插值参数，默认为2
    :param ifZ: 距离是否考虑高程，默认不考虑
    :param maxdistance: 站点影响的最大距离，默认100km
    :return: outData 各时间的网格降水，纬度：[ntimes, nrows, ncols]
    """
    nstation = station_xyz.shape[0]
    nrows = DEM.shape[0]
    ncols = DEM.shape[1]
    ntimes=outHourP.shape[0]
    a = np.zeros((nstation, nrows, ncols))
    outData = np.zeros((ntimes, nrows, ncols))
    lats = np.linspace(ymin + cellsize * (nrows - 1), ymin, nrows)
    lons = np.linspace(xmin, xmin + cellsize * (ncols - 1), ncols)
    xy=np.meshgrid(lons,lats)
    X=xy[0]
    Y=xy[1]
    # print(X)
    # for i in range(nrows):
    #     for j in range(ncols):
    #         X[i,j]=xmin+j*cellsize
    #         Y[i,j]=ymin+(nrows-i)*cellsize
    d = np.zeros((nstation, nrows, ncols))
    for k in range(nstation):
        if ifZ:
            d[k, :, :] = np.sqrt(np.power(X - station_xyz[k, 0], 2) + np.power(Y - station_xyz[k, 1], 2)+ np.power(DEM - station_xyz[k, 2], 2))
        else:
            d[k, :, :]=np.sqrt(np.power(X-station_xyz[k,0],2)+np.power(Y-station_xyz[k,1],2))
        a[k,:,:]=1.0/np.power(d[k,:,:],power)
        a[k, :, :][d[k,:,:]>maxdistance]=0
    sumidw=np.sum(a,axis=0)
    sumidw[sumidw==0]=1
    a=a/sumidw
    ab = a.reshape(nstation, nrows * ncols)#转为2为矩阵
    bb = np.dot(outHourP, ab)#降水和权重系数的矩阵相乘
    outData = bb.reshape((outData.shape))#
    return outData
def readgagexyz(gagesfile='gages.xlsx'):
    """
    :param filename: file name of rainfall excel file
    :param starttime: start time of rainfall
    :param endtime: end time of rainfall
    :param gagesfile: file name of rainfall gages
    :return: gages_xyz: x y,z of precipitation station [nstation,3]
             czbm: code of station
    """
    gf=pd.read_excel(gagesfile,sheet_name='Sheet1')
    czbm=gf['czbm']
    rgx=gf['x']
    rgy=gf['y']
    rgz=gf['z']
    gages_xyz = np.array((rgx, rgy, rgz)).T  # gages_xyz[nstations,3]
    return gages_xyz,czbm
def readgagerainfall(filename,starttime, endtime,nrg,czbm):
    """
    :param filename: file name of rainfall excel file
    :param starttime: start time of rainfall
    :param endtime: end time of rainfall
    :param nrg: number of rainfall gages
    :param czbm: code of rainfall gages
    :return: rfintensity:precipitation data  [ntimes,nstation],
    """
    start_time = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.datetime.strptime(endtime, '%Y-%m-%d %H:%M:%S')
    npair = int((end_time - start_time).total_seconds() / 3600)+1# n hours
    rfintensity = np.zeros((npair,nrg), dtype=np.float)
    irg = 0
    for sheetname in czbm:
        print(sheetname)
        tabler = pd.read_excel(filename,sheet_name=str(int(sheetname)))
        timer = tabler[u"Time"]
        rainfall = tabler[u'P']
        deltatime = start_time - timer[0]
        startrow = int(deltatime.total_seconds() / 3600)
        rfintensity[:,irg] = rainfall[startrow:startrow + npair]
        irg += 1
    return rfintensity

def writeNc(DEM, outData, xmin, ymin, cellsize, startTime, endTime,file_name='outIDWP.nc'):
    """
    environment: netCDF4,pandas,numpy
    station_xyz, x y,z of precipitation station [nstation,3]
    DEM, dem files [nrows,ncols]
    orgP,[ntimes,nstation],precipitation data
    xmin, min x of DEM data
    ymin, min y of DEM data
    cellsize, grid size
    startTime, start time of precp data,format('%Y-%m-%d %H:%M:%S')
    endTime, end time of precp data,format('%Y-%m-%d %H:%M:%S')
    """
    import netCDF4 as nc
    import pandas as pd
    import os
    nrows = DEM.shape[0]
    ncols = DEM.shape[1]
    ntimes = outData.shape[0]
    date_range = pd.date_range(startTime, endTime, periods=ntimes)
    lats = np.linspace(ymin + cellsize * (nrows-1), ymin, nrows)
    lons = np.linspace(xmin, xmin + cellsize * (ncols-1), ncols)
    if os.path.exists(file_name):
        os.remove(file_name)
    da = nc.Dataset(file_name, 'w', format="NETCDF4")
    da.createDimension('latitude', nrows)
    da.createDimension('longitude', ncols)
    da.createDimension('time', size=None)
    X = da.createVariable("X", 'f', ("longitude"))
    Y = da.createVariable("Y", 'f', ("latitude"))
    time = da.createVariable("time", 'S19', dimensions='time')
    X.units = 'meters east'
    Y.units = 'meters north'
    da.variables['Y'][:] = lats
    da.variables['X'][:] = lons
    da.times = time.shape[0]
    for itime in range(ntimes):
        time[itime] = date_range[itime].strftime('%Y-%m-%d %H:%M:%S')
    time.units = 'times since {0:s}'.format(time[0])
    da.createVariable('p', 'f8', ('time', 'latitude', 'longitude'))
    da.variables['p'][:] = outData
    da.close()
def plotgrid(outData,itime=0):
    """
    绘制网格图
    :return:
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    fig,ax=plt.subplots()
    fig.suptitle("IDW precpitation at Time %i h"%(itime+1))
    ax = sns.heatmap(outData[itime,:,:],cmap='jet',square=True)
    # ax.invert_yaxis()
    # plt.show()
    fig.savefig("out_pic/IDW_precpitation_at_Time_%i_h.png"%(itime+1))
    plt.close()
def plotline(outData,savetxt=True):
    import matplotlib.pyplot as plt
    # import seaborn as sns
    meanp=[]
    for i in range(outData.shape[0]):
        meanp.append(np.mean(outData[i,:,:]))
    fig,ax=plt.subplots(figsize=(10,7))
    ax.plot(meanp,'r')
    ax.set_xlabel("Time(h)")
    ax.set_ylabel("basin mean precip($mm$)")
    # plt.show()
    fig.savefig("meanprecip.png")
    plt.close()
    if savetxt:
        np.savetxt("meanprecip.txt",meanp,fmt="%.2f")


def creat_gif(gif_name, path, duration=0.3):
    '''
    生成gif文件，原始图片仅支持png格式
    gif_name ： 字符串，所生成的 gif 文件名，带 .gif 后缀
    path :      需要合成为 gif 的图片所在路径
    duration :  gif 图像时间间隔
    '''
    import imageio,os
    frames = []
    pngFiles = os.listdir(path)
    inpng = []
    for i in range(len(pngFiles)):
        inpng.append("IDW_precpitation_at_Time_%i_h.png" % (i + 1))
    # pngFiles.sort()
    image_list = [os.path.join(path, f) for f in inpng]
    for image_name in image_list:
       frames.append(imageio.imread(image_name))
    imageio.mimsave(gif_name, frames, 'GIF', duration=duration)
    return
def readNC(ncfile):
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
    # time = (nc_obj.variables['time'][:])
    # X = (nc_obj.variables['X'][:])
    # Y = (nc_obj.variables['Y'][:])
    # Q = (nc_obj.variables['p'][:])