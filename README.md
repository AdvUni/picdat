# PicDat

The aim of PicDat is to provide better insight to performance data from NetApp
controllers. There is a utitily from NetApp called PerfStat which allows to
collect a huge number of performance counters. The drawback is that PerfStat
generates one large text file, which is very cumbersome to analyse. 

PicDat selects some of the counters which are typically sufficient for the 
analysis and writes them to several csv files. 

To generate graphs we use the tool dygraphs in a second step.

Example output:

````
python3 picdat.py
Welcome to PicDat!
Please enter a path to a PerfStat output file: </path/to/perfstat.out>
Please select a destination directory for the results: </path/to/output>
Read data...
Planned number of iterations was executed correctly.
Prepare directory...
Create csv tables...
Wrote graph values into /path/to/output/results/aggregate_total_transfers_graph_values.csv
Wrote graph values into /path/to/output/results/processor_processor_busy_graph_values.csv
Wrote graph values into /path/to/output/results/volume_total_ops_graph_values.csv
Wrote graph values into /path/to/output/results/volume_avg_latency_graph_values.csv
Wrote graph values into /path/to/output/results/volume_read_data_graph_values.csv
Wrote graph values into /path/to/output/results/lun_total_ops_graph_values.csv
Wrote graph values into /path/to/output/results/lun_avg_latency_graph_values.csv
Wrote graph values into /path/to/output/results/lun_read_data_graph_values.csv
Create html file...
Done. You will find graphs under: /path/to/output/results/graphs.html
````
