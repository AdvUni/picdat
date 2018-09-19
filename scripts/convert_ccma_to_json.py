"""
This is a script for operating a Trafero container to convert ccma files in ASUPs into readable
json. Place a config.yml file like the example_config.yml in the same location as the script and
run it with an ASUP tgz file you want to convert. It will return write several json files to an
output directory you specified.
"""
import logging
import os
import sys
import shutil
import getopt
import tarfile
import uuid
import yaml
import requests

__author__ = 'Marie Lohbeck'
__copyright__ = 'Copyright 2018, Advanced UniByte GmbH'


def get_log_level(log_level_string):
    """
    Turns a string into a log level, the logging module can understand
    :param log_level_string: A String representing a log level like 'info' or 'error'.
    :return: A constant from the logging module, representing a log level.
    """
    log_level_dict = {
        'debug': logging.DEBUG,
        'DEBUG': logging.DEBUG,
        'info': logging.INFO,
        'INFO': logging.INFO,
        'warning': logging.WARNING,
        'WARNING': logging.WARNING,
        'error': logging.ERROR,
        'ERROR': logging.ERROR,
        'critical': logging.CRITICAL,
        'CRITICAL': logging.CRITICAL
    }
    try:
        return log_level_dict[log_level_string]
    except KeyError:
        logging.error('No log level like \'%s\' exists. Try one of those: %s', log_level_string,
                      [entry for entry in log_level_dict])
        sys.exit(1)


def handle_user_input(argv):
    """
    Processes command line options. If no input file or output directory is given, ask the user at
    runtime. If a log file is desired, logging content is redirected into conversion.log.
    :param argv: Command line parameters.
    :return: absolute paths to input and output
    """
    # get all options from argv and turn them into a dict
    try:
        opts, _ = getopt.getopt(argv[1:], 'hld:i:o:',
            ['help', 'logfile', 'debug=', 'input=', 'outputdir='])
        opts = dict(opts)
    except getopt.GetoptError:
        logging.error('Couldn\'t read command line options.')

    # print help information if option 'help' is given
    if '-h' in opts or '--help' in opts:
        print('''
usage: %s [--help] [--input "input"] [--outputdir "output"] [--debug "level"]

    --help, -h: prints this message
                      
    --input "input", -i "input": input is the path to an ASUP tgz
                                 
    --outputdir "output", -o "output": output is the directory's path, where this program puts its
                                       results. If there is no directory existing yet under this
                                       path, one would be created.
                                       
    --debug "level", -d "level": level should be inside debug, info, warning, error, critical. It
                                 describes the filtering level of command line output during
                                 running this program. Default is "info".
                                 
    --logfile, -l: redirects logging information into a file called conversion.log.
        ''' % argv[0])

    # extract log level from options if possible
    if '-d' in opts:
        log_level = get_log_level(opts['-d'])
    elif '--debug' in opts:
        log_level = get_log_level(opts['--debug'])
    else:
        log_level = logging.INFO

    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=log_level)

    # extract inputfile from options if possible
    if '-i' in opts:
        input_file = opts['-i']
    elif '--input' in opts:
        input_file = opts['--input']
    else:
        while True:
            input_file = input('Please enter a path to a ASUP tgz:' + os.linesep)

            if os.path.isfile(input_file):
                break
            else:
                print('This file does not exist. Try again.')
    if not os.path.isfile(input_file):
        print('input file does not exist.')
        sys.exit(1)

    # extract outputdir from options if possible
    if '-o' in opts:
        output_dir = opts['-o']
    elif '--outputdir' in opts:
        output_dir = opts['--outputdir']
    else:
        output_dir = input('Please select a destination directory for the json files. ('
                                      'Default is ./picdat_json_files):' + os.linesep)
        if output_dir == '':
            output_dir = 'picdat_json_files'

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # decide, whether logging information should be written into a log file
    if '-l' in opts or '--logfile' in opts:
        _ = [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=output_dir
                            +os.sep + 'conversion.log', level=log_level)

    logging.info('inputfile: %s, outputdir: %s', os.path.abspath(input_file), os.path.abspath(
        output_dir))

    return os.path.abspath(input_file), os.path.abspath(output_dir)


def read_config():
    """
    Reads config.yml file.
    :return: path to Trafero collector, Trafero's address, dict of objects and counters.
    """
    try:
        with open('config.yml', 'r') as ymlfile:
            cfg = yaml.load(ymlfile)

        trafero_in_dir = cfg['trafero_in_dir']
        trafero_address = cfg['trafero_address']
        objects = cfg['objects']

        return trafero_in_dir, trafero_address, objects
    except FileNotFoundError:
        logging.error('No config file. Script needs a file named config.yml in the same location.')
        sys.exit(1)
    except KeyError:
        logging.error('Invalid config file. config.yml needs to include entries '
                      '"trafero_in_dir", "trafero_address" and "objects".')
        sys.exit(1)


def unpack_to_collector(abs_asup_path, input_file):
    """
    Unpacks the ASUP inside the Trafero's collector.
    :param abs_asup_path: absolute path to an empty directory inside Trafero collector, where ASUP
    should be extracted to.
    :param input_file: path to ASUP tgz file.
    :return: None.
    """
    try:
        with tarfile.open(input_file, 'r') as tar:
            tar.extractall(abs_asup_path)

        if 'CM-STATS-HOURLY-INFO.XML' in os.listdir(abs_asup_path) \
        and 'CM-STATS-HOURLY-DATA.XML' in os.listdir(abs_asup_path):
            logging.info('Found files called CM-STATS-HOURLY-INFO.XML and CM-STATS-HOURLY-DATA.XML'
                         ' in your ASUP. This means probably, that your performance data has xml '
                         'format and not ccma. Trafero is not able to convert it. But, if you '
                         'wish to visualise the ASUP, just pass it directly to PicDat.')
            sys.exit(0)

    except tarfile.ReadError:
        logging.error(
            'File you gave as input is not a tar file. Input must be an ASUP tgz archive!')
        sys.exit(1)


def get_list_string(some_list):
    """
    Creates a string like '["a","b","c"]. The only difference from list's own str method is to use
    double quotes " instead of single quotes '. Necessary for Trafero understanding the requests.
    :param some_list: list
    :return: string with some_list's content.
    """
    list_string = '['
    for element in some_list:
        list_string += '"' + str(element) + '"'
        list_string += ','
    if some_list:
        list_string = list_string[:-1]
    list_string += ']'
    return list_string


def ingest_into_trafero(header, objects_counters_dict, asup_path, trafero_address):
    """
    Sends a ingest request to Trafero over http (POST).
    :param header: dict containing the headers for Trafero requests.
    :param objects_counters_dict: dict, mapping counters like 'total_ops', 'read_data', ... to
    objects like 'aggregate', 'processor',...
    :param asup_path: relative path to directory, in which the ASUP is extracted to. Relative means
    here, relative to the Trafero collector dir which is the /ccma directory from Trafero's sight.
    :param trafero_address: Adress of Trafero container.
    """
    objects_str = get_list_string((list(objects_counters_dict.keys())))
    data = '{"ccma_dir_path":"","ingest_type":"asup","asup_dir_path":"%s","object_filter":%s,' \
    '"display_all_zeros":false}' % (asup_path, objects_str)
    logging.debug('payload ingest request: %s', data)

    url = '%s/api/manage/ingest/' % trafero_address
    logging.debug('url ingest request: %s', url)

    response = requests.post(url, headers=header, data=data)
    logging.debug('ingest response: %s', response.text)

    try:
        cluster_uuid = response.json()['ingest_results'][0]['cluster_uuid']
        node_uuid = response.json()['ingest_results'][0]['node_uuid']
        logging.debug('cluster uuid: %s, node uuid: %s', cluster_uuid, node_uuid)
        return cluster_uuid, node_uuid

    except KeyError:
        logging.error(
            'Tried to read cluster and node name from Trafero\'s response, but is has not '
            'expected format. Probably, something went wrong. Here is the response: %s',
            response.text)
        sys.exit(1)


def retrieve_values(header, objects_counters_dict, cluster, node, trafero_address, output_dir):
    """
    Sends several retrieve-values requests to Trafero over http (GET).
    Sends one request per object in config.yml.
    :param header: dict containing the headers for Trafero requests.
    :param objects_counters_dict: dict, mapping counters like 'total_ops', 'read_data', ... to
    objects like 'aggregate', 'processor',...
    :param cluster: The cluster name of the ASUP where function should retrieve values from.
    :param node: The node name of the ASUP where function should retrieve values from.
    :param trafero_address: Adress of Trafero container.
    :param output_dir: Path to directory where to write json files with values.
    """
    url = '%s/api/retrieve/values/' % trafero_address
    logging.debug('url retrieve values request: %s', url)

    for obj, counters in objects_counters_dict.items():

        logging.debug('counters (%s): %s', obj, counters)
        counter_string = get_list_string(counters)

        data = '{"cluster":"%s","node":"%s","object_name":"%s","counter_name":"",'\
        '"counter_names":%s,"instance_name":"","x_label":"","y_label":"","time_from":0,'\
        '"time_to":0,"summary_type":"","best_effort":false,"raw":false}' \
        % (cluster, node, obj, counter_string)
        logging.debug('payload retrieve values request (%s): %s', obj, data)

        value_file = os.path.join(output_dir, str(obj) + '.json')

        with requests.get(url, headers=header, data=data, stream=True) as response:
            with open(value_file, 'wb') as values:
                for chunk in response.iter_content(chunk_size=1024):
                    logging.debug('chunk (obj: %s): %s', obj, chunk)
                    values.write(chunk)

        logging.info('Wrote values in file %s', value_file)

def delete_from_trafero(header, cluster, node, trafero_address):
    """
    Sends a delete request to Trafero over http (DELETE).
    :param header: dict containing the headers for Trafero requests.
    :param cluster: The cluster name of the ASUP which function should delete.
    :param node: The node name of the ASUP which function should delete.
    :param trafero_address: Adress of Trafero container.
    """
    url = '%s/api/manage/delete/' % trafero_address
    logging.debug('url delete request: %s', url)

    data = '{"cluster":"%s","node":"%s"}' % (cluster, node)
    logging.debug('payload delete request: %s', data)

    requests.delete(url, headers=header, data=data)


# constant dict to send as headers in http requests
REQUEST_HEADER = {'Content-Type': 'application/json', 'Accept': 'application/json'}

# read user arguments
INPUT_FILE, OUTPUT_DIR = handle_user_input(sys.argv)

# read config.yml file
TRAFERO_COLLECTOR, TRAFERO_ADDRESS, OBJECTS_COUNTERS_DICT = read_config()

# create directory with random name in Trafero collector
while True:
    ASUP_PATH = str(uuid.uuid4())
    ABS_ASUP_PATH = os.path.join(TRAFERO_COLLECTOR, ASUP_PATH)
    try:
        os.makedirs(ABS_ASUP_PATH)
        break
    except FileExistsError:
        logging.debug('random file name already exists: %s, create new file name', ASUP_PATH)
logging.debug('ASUP location inside Trafero: %s', ASUP_PATH)

try:
    # unpack ASUP inside Trafero collector directory
    logging.info('Extract ASUP into Trafero collector directory...')
    unpack_to_collector(ABS_ASUP_PATH, INPUT_FILE)

    # Trafero ingest: Upload ccmas in ASUP to Trafero database
    logging.info('Ingest ASUP in Trafero...')
    CLUSTER, NODE = ingest_into_trafero(
        REQUEST_HEADER, OBJECTS_COUNTERS_DICT, ASUP_PATH, TRAFERO_ADDRESS)

    # Trafero retrieve values: Download data in json format from Trafero database
    logging.info('Retrieve values from Trafero...')
    retrieve_values(
        REQUEST_HEADER, OBJECTS_COUNTERS_DICT, CLUSTER, NODE, TRAFERO_ADDRESS, OUTPUT_DIR)

    # Trafero delete: Remove ASUP from Trafero database
    logging.info('Delete ASUP from Trafero...')
    delete_from_trafero(REQUEST_HEADER, CLUSTER, NODE, TRAFERO_ADDRESS)

    logging.info('Done. You will find json files converted from ASUP under %s. You can now pass'
                 'this directory to PicDat.', OUTPUT_DIR)


finally:
    # remove ASUP from Trafero collector directory
    shutil.rmtree(ABS_ASUP_PATH)
    logging.info('(Temporarily extracted ASUP in Trafero collector directory deleted)')
