# picdat

The aim of picdat is to provide better insight to performance data from NetApp controllers. There is a utitily from NetApp called perfstat which allows to collect a huge number of performance counters. The drawback is that perfstat generates one large textfile which is very cumbersome to analyse. picdat selects some of the numbers which are typically sufficient for the analysis and writes several csv files. To generate graphs we use the tool dygraph in a second step.
