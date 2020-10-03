# -*- coding: utf-8 -*-
"""
Created on 2020/10/03 By 文磊
contact=wenlei6037@hhu.edu.cn
author wenlei
"""
from InterpolationQ import interQ

filename='Siqian_Q.xls'
ItQ=interQ(60)
ItQ.readQ(filename)
ItQ.interQ()
ItQ.saveQ("司前流量.xlsx")
ItQ.plotHQ()
ItQ.plotHQline()