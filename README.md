# PicDat #

The aim of PicDat is to provide better insight into performance data from NetApp
controllers. There is a utitily from NetApp called PerfStat which can collect
a huge number of performance counters. The main drawback is that PerfStat
generates one large text file, often more than 100 mb in size, which is very
cumbersome to analyze.

PicDat selects some of the counters which are typically sufficient for
performance analysis, and writes them to seperate csv files.

Additionally, PicDat can handle ASUP xml performance data, that can be downloaded
from the NetApp support site.

To generate the graphs, PicDat uses the tool dygraphs in a second step.

## General usage: ##

````
picdat [--help] [--sortbyname] [--inputfile "input"] [--outputdir "output"] [--debug "level"] [--logfile]
````


## Example output: ##

````
python picdat.py -i"</path/to/input>" -o"</path/to/output>" 
2018-03-09 12:00:35,195 INFO: inputfile: </path/to/input>, outputdir: </path/to/output>
2018-03-09 12:00:35,196 INFO: Prepare directory...
2018-03-09 12:00:35,202 INFO: Running PicDat in PerfStat mode
2018-03-09 12:00:35,202 INFO: Did not find a console.log file to extract perfstat's cluster and node name.
2018-03-09 12:00:35,202 INFO: Read data...
2018-03-09 12:00:37,796 INFO: Planned number of iterations was executed correctly.
2018-03-09 12:00:37,798 INFO: Create csv tables...
2018-03-09 12:00:37,799 INFO: Wrote chart values into /path/to/output/tables/aggregate_total_transfers_chart_values.csv
2018-03-09 12:00:37,799 INFO: Wrote chart values into /path/to/output/tables/processor_processor_busy_chart_values.csv
2018-03-09 12:00:37,799 INFO: Wrote chart values into /path/to/output/tables/volume_read_ops_chart_values.csv
2018-03-09 12:00:37,801 INFO: Wrote chart values into /path/to/output/tables/volume_write_ops_chart_values.csv
2018-03-09 12:00:37,801 INFO: Wrote chart values into /path/to/output/tables/volume_other_ops_chart_values.csv
2018-03-09 12:00:37,801 INFO: Wrote chart values into /path/to/output/tables/volume_total_ops_chart_values.csv
2018-03-09 12:00:37,802 INFO: Wrote chart values into /path/to/output/tables/volume_avg_latency_chart_values.csv
2018-03-09 12:00:37,802 INFO: Wrote chart values into /path/to/output/tables/volume_read_data_chart_values.csv
2018-03-09 12:00:37,802 INFO: Wrote chart values into /path/to/output/tables/volume_write_data_chart_values.csv
2018-03-09 12:00:37,807 INFO: Wrote chart values into /path/to/output/tables/sysstat_1sec_percent_chart_values.csv
2018-03-09 12:00:37,819 INFO: Wrote chart values into /path/to/output/tables/sysstat_1sec_MBs_chart_values.csv
2018-03-09 12:00:37,828 INFO: Wrote chart values into /path/to/output/tables/sysstat_1sec_IOPS_chart_values.csv
2018-03-09 12:00:37,830 INFO: Wrote chart values into /path/to/output/tables/statit_disk_statistics_chart_values.csv
2018-03-09 12:00:37,831 INFO: Create html file...
2018-03-09 12:00:37,833 INFO: Generated html file at /path/to/output/charts.html
2018-03-09 12:00:37,843 INFO: Done. You will find charts under: </path/to/output>
````

## Requirements: ##

The following Python modules are required to run PicDat:

* ijson
* tzlocal
* pytz

The script `convert_ccma_to_json` requires:

* yaml
* requests

