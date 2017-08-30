# PicDat

The aim of PicDat is to provide better insight to performance data from NetApp controllers. There is a utitily from NetApp called PerfStat which allows to collect a huge number of performance counters. The drawback is that PerfStat generates one large textfile which is very cumbersome to analyse. PicDat selects some of the numbers which are typically sufficient for the analysis and writes several csv files. To generate graphs we use the tool dygraphs in a second step.
