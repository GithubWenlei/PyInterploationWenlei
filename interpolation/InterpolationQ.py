# -*- coding: utf-8 -*-
"""
Created on 2020/10/03 By 文磊
contact=wenlei6037@hhu.edu.cn
author wenlei
"""
from pandas import DataFrame,Series
from datetime import timedelta
from numpy import interp as interp
import numpy as np
import pandas as pd
class interQ():
    def __init__(self,deltaTimeMin):
        print()
        self.deltaTimeMin=deltaTimeMin
        self.IsStage = False
        self.IsDischarge = False
    def readQ(self,filename):
        xls = pd.ExcelFile(filename)
        table1 = xls.parse(0)  # xls.parse("Sheet1")
        self.nrows=table1.shape[0]
        try:
            for key in table1.keys():
                if "测站" in key or "STCD" in key:
                    self.stcd = table1[key]
                if "时间" in key or "time" in key or "Time" in key or "TM" in key:
                    self.Time = table1[key]
                if "流量" in key or "Q" in key:
                    self.IsDischarge=True
                    self.Discharge = table1[key]
                if "水位" in key or "Z" in key:
                    self.IsStage=True
                    self.stage = table1[key]
        except Exception as e:
            print(e)
    def ntimes(selfself, start_time, end_time, deltaTimeMin):
        return int((end_time - start_time).total_seconds() / 60 / deltaTimeMin) + 1
    def deltaMin(self,startT,endT):
        return np.int((startT - endT).total_seconds() / 60)
    def interQ(self):
        print('start time is :', self.Time[0])
        print('end time is :', self.Time[len(self.Time) - 1])
        totalMin = self.deltaMin(self.Time[len(self.Time) - 1], self.Time[0])
        outN = int(totalMin / self.deltaTimeMin)
        m = self.Time[0].minute
        if m == 0:
            outStartTime = self.Time[0]
            outEndTime = outStartTime + timedelta(minutes=self.deltaTimeMin * outN)
        else:
            outStartTime = self.Time[0] + timedelta(minutes=(-m))
            outEndTime = outStartTime + timedelta(minutes=self.deltaTimeMin * outN)
        self.outTime = pd.date_range(outStartTime, outEndTime, periods=outN + 1)
        if self.IsDischarge:
            print("根据时间序列插值流量")
            self.outDischarge = interp(self.outTime, self.Time, self.Discharge)
        else:
            print("No Discharge input in the excel file")
        if self.IsStage:
            print("根据时间序列插值水位")
            self.outStage = interp(self.outTime, self.Time, self.stage)
        else:
            print("No Stage input in the excel file")

    def saveQ(self,outfilename):
        writer = pd.ExcelWriter(outfilename)
        self.out_excel = DataFrame()
        # out_excel['测站编码']=Series(self.stcd)
        self.out_excel['时间'] = Series(self.outTime)
        if self.IsDischarge:
            self.out_excel['流量(m^3/s)'] = Series(self.outDischarge)
        if self.IsStage:
            self.out_excel['水位(m)'] = Series(self.outStage)
        self.out_excel.to_excel(writer, sheet_name=str(int(self.stcd[0])), header=True, index=False)  # 该行代码用时最多
        writer.save()
    def plotHQ(self):
        import seaborn as sns
        import matplotlib.pyplot as plt
        from scipy.optimize import curve_fit
        sns.set(palette='RdBu')
        self.plotdata = DataFrame()
        self.plotdata['Discharge($m^3/s$)'] = Series(self.Discharge)
        self.plotdata['stage(m)'] = Series(self.stage)
        #拟合水位流量关系，采用预定义的func函数，这里定义的是二次多项式函数，可以定义为其他函数。
        popt,pcov = curve_fit(self.func,np.array(self.stage),np.array(self.Discharge))
        y_pred=[self.func(i,popt[0],popt[1],popt[2])for i in np.array(self.stage)]
        #拟合后的值为y_pred
        sns.relplot(x='stage(m)',y='Discharge($m^3/s$)',data=self.plotdata,label="discharge")
        # sns.lmplot(x='stage(m)',y='Discharge($m^3/s$)',ci=60,data=self.plotdata)
        # sns.stripplot(x='stage(m)',y='Discharge($m^3/s$)',data=self.plotdata)
        plt.plot(self.stage,y_pred,"b*",label='fit_value')
        plt.legend()
        plt.show()
    def func(self,x,a,b,c):
        # return b * np.power(x,a) + c
        return a*x**2+b*x+c
    def plotHQline(self):
        import matplotlib.pyplot as plt
        fig,host=plt.subplots()
        plt.subplots_adjust(top=0.88,
                        bottom=0.3,
                        left=0.13,
                        right=0.9,
                        hspace=0.2,
                        wspace=0.2)
        par=host.twinx()
        a,=host.plot(self.Discharge,'r-',label='Discharge($m^3/s$)')
        b,=par.plot(self.stage,'g',label='Stage(m)')
        host.set_ylabel("Discharge($m^3/s$)")
        par.set_ylim(min(self.stage), max(self.stage) * 2)
        host.set_ylim(min(self.Discharge), max(self.Discharge) * 2)
        par.set_ylabel("Stage(m)")
        par.invert_yaxis()
        xticks=np.linspace(0,len(self.stage)-1,5)
        xtickslabels=[self.Time[int(n)].strftime('%Y-%m-%d %H:%M') for n in xticks]
        host.set_xticks(xticks)
        host.set_xticklabels(xtickslabels,rotation=30)
        plt.legend((a,b),("Discharge","Stage"),ncol=2,bbox_to_anchor=(0.35,1.01))
        plt.show()