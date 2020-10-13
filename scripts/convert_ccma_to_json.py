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

# constant dict to send as headers in http requests
REQUEST_HEADER = {'Content-Type': 'application/json', 'Accept': 'application/json'}


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
                      
    --input "input", -i "input": input is the path to an ASUP tgz archive or to a directory. In
                                 case of a directory, it must either contain several ASUP tgz
                                 archives belonging all to the same cluster and node, or several
                                 ccma files, which are files ending with 'ccma.gz' or 'ccma.meta'.
                                 
    --outputdir "output", -o "output": output is the directory's path where the results will be
                                       put. If the directory does not exist yet, it will be created.
                                       
    --debug "level", -d "level": level must be one of debug, info, warning, error, critical. It
                                 specifies the diagnostic level of the console output of this
                                 program. Default is "info".
                                 
    --logfile, -l: redirects logging information into a file called conversion.log.
        ''' % argv[0])

        sys.exit(0)

    # extract log level from options if possible
    if '-d' in opts:
        log_level = get_log_level(opts['-d'])
    elif '--debug' in opts:
        log_level = get_log_level(opts['--debug'])
    else:
        log_level = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
    logging.getLogger().setLevel(log_level)
    # suppress warnings from request logger
    logging.getLogger('urllib3').setLevel(logging.ERROR)

    # extract input from options if possible
    if '-i' in opts:
        input_data = opts['-i']
    elif '--input' in opts:
        input_data = opts['--input']
    else:
        while True:
            input_data = input('Please enter a path to an ASUP tgz file, or to a directory with several '
                               'tgz or ccma files:' + os.linesep)

            if os.path.isfile(input_data) or os.path.isdir(input_data):
                break
            else:
                print('This file/directory does not exist. Try again.')
    if not os.path.isfile(input_data) and not os.path.isdir(input_data):
        print('Path %s does not exist.' % input_data)
        sys.exit(1)

    # extract outputdir from options if possible
    if '-o' in opts:
        output_dir = opts['-o']
    elif '--outputdir' in opts:
        output_dir = opts['--outputdir']
    else:
        output_dir = input('Please enter a destination directory for the json files. ('
                                      'Default is ./picdat_json_files):' + os.linesep)
        if output_dir == '':
            output_dir = 'picdat_json_files'

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # decide, whether logging information should be written into a log file
    if '-l' in opts or '--logfile' in opts:
        _ = [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=output_dir
                            +os.sep + 'conversion.log')
        logging.getLogger().setLevel(log_level)
        # suppress warnings from request logger
        logging.getLogger('urllib3').setLevel(logging.ERROR)

    logging.info('inputfile: %s, outputdir: %s', os.path.abspath(input_data), os.path.abspath(
        output_dir))

    return os.path.abspath(input_data), os.path.abspath(output_dir)


def read_config():
    """
    Reads config.yml file.
    :return: path to location, which is mapped to Trafero's 'ccma' volume; Trafero's address; dict
    of objects and counters.
    """
    try:
        with open('config.yml', 'r') as ymlfile:
            cfg = yaml.load(ymlfile)

        trafero_in_dir = cfg['trafero_in_dir']
        trafero_address = cfg['trafero_address']
        objects = cfg['objects']

        return trafero_in_dir, trafero_address, objects
    except FileNotFoundError:
        logging.error('No config file. This script needs a file called config.yml in the working directory.')
        sys.exit(1)
    except KeyError:
        logging.error('Invalid config file. config.yml needs to include entries '
                      '"trafero_in_dir", "trafero_address" and "objects".')
        sys.exit(1)


def determine_input(input_data):
    """
    Decides whether input is of ingest_type 'asup' or 'ccma'.
    :param input_data: The script's user input.
    :return: A list and a Boolean. The list contains all absolute file paths of the input, which
    have file extension 'tgz'. The boolean says, whether input data is of kind 'asup' (or 'ccma',
    if False). If the boolean is False, which means, the data is of kind 'ccma', the list is empty.
    """

    if os.path.isfile(input_data):
        return [input_data], True

    elif os.path.isdir(input_data):
        if any(['ccma' in filename for filename in os.listdir(input_data)]):
            return [], False

        return [os.path.join(input_data, file) for file in os.listdir(input_data)
                if file.split('.')[-1] == 'tgz'], True
    return None


def copy_ccmas(source_dir, destination_dir):
    """
    Copies all files from source_dir to destination_dir, which contain 'ccma' in their names.
    :param: destination_dir: destination directory.
    :param: source_dir: source directory.
    """
    for filename in os.listdir(source_dir):
        if 'ccma' in filename:
            shutil.copyfile(
                os.path.join(source_dir, filename), os.path.join(destination_dir, filename))


def unpack_tgz(destination_dir, tgz):
    """
    Unpacks an ASUP tgz file into destination directory.
    :param destination_dir: absolute path to an empty directory for unpacking tgz inside. Should
    probably be inside the location, which is mapped to the Trafero volume 'ccma'.
    :param tgz: path to ASUP tgz file.
    :return: None.
    """

    try:
        with tarfile.open(tgz, 'r') as tar:
            tar.extractall(destination_dir)

        if 'CM-STATS-HOURLY-INFO.XML' in os.listdir(destination_dir) \
        and 'CM-STATS-HOURLY-DATA.XML' in os.listdir(destination_dir):
            logging.info('Found files called CM-STATS-HOURLY-INFO.XML and CM-STATS-HOURLY-DATA.XML'
                         'in your ASUP. This probably means that your performance data is in xml '
                         'format instead of ccma. Trafero is not able to convert it. If you '
                         'want to visualise the ASUP, just pass it to PicDat directly.')
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


def handle_retrieve_error(unexpected_response):
    """
    If retrieve request fails, there are some known error messages. Here, they get caught to
    provide the user with more information about this error and to tell him, how he can fix it.
    :param unexpected_response: http response which probably contains an error.
    :return: (cluster, node) or (None, None)
    """
    if 'errors' in unexpected_response.json():
        if 'message' in unexpected_response.json()['errors']:
            # Handle error message, that ASUP is invalid:
            if unexpected_response.json()['errors']['message'] == 'Invalid ASUP directory. ' \
            'Cannot find either hourly or event files in the directory':
                logging.warning('Trafero rejects ASUP. It seems not to contain the expected '
                                'performance data. Trafero usually expects either a '
                                'PERFORMANCE-ARCHIVES.TAR or several '
                                'CM-STATS-HOURLY-DATA-**.TAR archives inside the ASUP.')
                return None, None

    elif 'ingest_results' in unexpected_response.json():
        if 'errors' in unexpected_response.json()['ingest_results'][0]:
            if 'message' in unexpected_response.json()['ingest_results'][0]['errors']:
            # Handle ccmas, which are already ingested:
                if 'File already ingested' in unexpected_response.json(
                    )['ingest_results'][0]['errors']['message']:
                    logging.error('It seems like some or all of the ccma files from your input '
                                  'are already ingested in Trafero. Unfortunately, Trafero does not '
                                  'specify in its response for which cluster/node the ccma files are '
				  'already ingested. So, this program cannot continue with '
                                  'retrieving values from these files. Can you manually enter the '
                                  'cluster and the node name? Otherwise, just press Enter and fix '
				  'this issue by deleting everything from the folder which is mapped '
                                  'to Trafero\'s "hdf5" volume, and then running this script again.')
                    cluster = input('Please enter cluster name: ')
                    if not cluster:
                        logging.info('Quit Program.')
                        sys.exit(1)
                    node = input('Please enter node name: ')
                    if not node:
                        logging.info('Quit Program.')
                        sys.exit(1)
                    return cluster, node

    logging.error(
        'Tried to read cluster and node name from Trafero\'s unexpected_response, but is was not '
        'in an expected format. Probably, something went wrong. Here is the unexpected_response: %s',
        unexpected_response.text)
    return None, None


def ingest_into_trafero(objects_counters_dict, data_path, trafero_address, is_asup):
    """
    Sends a ingest request to Trafero over http (POST).
    :param objects_counters_dict: dict, mapping counters like 'total_ops', 'read_data', ... to
    objects like 'aggregate', 'processor',...
    :param data_path: relative path to directory, in which the ASUP is extracted to. Relative means
    here, relative to the Trafero 'ccma' volume.
    :param trafero_address: Adress of Trafero container.
    """
    objects_str = get_list_string(list(objects_counters_dict.keys()))

    if is_asup:
        ingest_type = 'asup'
        ccma_dir_path = ''
        asup_dir_path = data_path
    else:
        ingest_type = 'ccma'
        ccma_dir_path = data_path
        asup_dir_path = ''

    data = '{"ccma_dir_path":"%s","ingest_type":"%s","asup_dir_path":"%s","object_filter":%s,' \
    '"display_all_zeros":false}' % (ccma_dir_path, ingest_type, asup_dir_path, objects_str)
    logging.debug('payload ingest request: %s', data)

    url = '%s/api/manage/ingest/' % trafero_address
    logging.debug('url ingest request: %s', url)

    response = requests.post(url, headers=REQUEST_HEADER, data=data)
    logging.debug('ingest response: %s', response.text)

    try:
        cluster_uuid = response.json()['ingest_results'][0]['cluster_uuid']
        node_uuid = response.json()['ingest_results'][0]['node_uuid']
        logging.debug('cluster uuid: %s, node uuid: %s', cluster_uuid, node_uuid)
        return cluster_uuid, node_uuid

    except KeyError:
        return handle_retrieve_error(response)


def retrieve_values(objects_counters_dict, cluster, node, trafero_address, destination_dir):
    """
    Sends several retrieve-values requests to Trafero over http (GET).
    Sends one request per object in config.yml.
    :param objects_counters_dict: dict, mapping counters like 'total_ops', 'read_data', ... to
    objects like 'aggregate', 'processor',...
    :param cluster: The cluster name of the ASUP where function should retrieve values from.
    :param node: The node name of the ASUP where function should retrieve values from.
    :param trafero_address: Adress of Trafero container.
    :param destination_dir: Path to directory where to write json files with values.
    """
    url = '%s/api/retrieve/values/' % trafero_address
    logging.debug('url retrieve values request: %s', url)

    for obj, counters in objects_counters_dict.items():

        logging.debug('counters (%s): %s', obj, counters)
        counter_string = get_list_string(counters)

        data = '{"cluster":"%s","node":"%s","object_name":"%s","counter_name":"",'\
        '"counter_names":%s,"instance_name":"","x_label":"","y_label":"","time_from":0,'\
        '"time_to":0,"summary_type":"","best_effort":true,"raw":false}' \
        % (cluster, node, obj, counter_string)
        logging.debug('payload retrieve values request (%s): %s', obj, data)

        value_file = os.path.join(destination_dir, str(obj) + '.json')

        with requests.get(url, headers=REQUEST_HEADER, data=data, stream=True) as response:
            if response.status_code == 200:
                with open(value_file, 'wb') as values:
                    for chunk in response.iter_content(chunk_size=1024):
                        logging.debug('chunk (obj: %s): %s', obj, chunk)
                        values.write(chunk)
                logging.info('Wrote values in file %s', value_file)
            else:
                logging.warning('Got response with status code != 200 for object %s. Error '
                                'message: %s', obj, response.text)


def delete_from_trafero(cluster, node, trafero_address):
    """
    Sends a delete request to Trafero over http (DELETE).
    :param cluster: The cluster name of the ASUP which function should delete.
    :param node: The node name of the ASUP which function should delete.
    :param trafero_address: Adress of Trafero container.
    """
    url = '%s/api/manage/delete/' % trafero_address
    logging.debug('url delete request: %s', url)

    data = '{"cluster":"%s","node":"%s"}' % (cluster, node)
    logging.debug('payload delete request: %s', data)

    response = requests.delete(url, headers=REQUEST_HEADER, data=data)
    logging.debug('delete response: %s', response)

    if response.status_code != 200:
        logging.error('Deletion from Trafero failed. Here is Trafero\'s response: %s',
                        response.text)


def create_random_dir(location):
    """
    Creates a unique directory with a random name inside 'location'.
    :param location: Path to the location, where random dir should get created.
    :return: Name of random directory.
    """
    # create directory with random name inside location, which is mapped to Trafero's 'ccma' volume
    while True:
        random_dir = str(uuid.uuid4())
        try:
            os.makedirs(os.path.join(location, random_dir))
            return random_dir
        except FileExistsError:
            logging.debug('random file name already exists: %s, generating new file name', random_dir)


def run_conversion():
    """
    Runs script. Gets called at the bottom of this module.
    """

    # read user arguments
    input_data, output_dir = handle_user_input(sys.argv)

    # read config.yml file
    trafero_ccma_volume, trafero_address, objects_counters_dict = read_config()

    # create directory with random name inside location, which is mapped to Trafero's 'ccma' volume
    working_dir = create_random_dir(trafero_ccma_volume)
    logging.debug('Location of working directory inside Trafero: %s', working_dir)

    try:
        # decide, whether data is of kind 'asup' or 'ccma' and create list of all asup tgz files
        tgz_files, is_asup = determine_input(input_data)

        # initialise cluster and node
        cluster = None
        node = None

        if is_asup:
            logging.debug('Ingest type is "asup"')
            for tgz in tgz_files:
                # create directory with random name inside working_dir
                asup_dir = create_random_dir(os.path.join(trafero_ccma_volume, working_dir))

                # unpack ASUP inside asup_dir
                logging.info('Extract ASUP %s into Trafero\'s \'ccma\' volume...', tgz)
                logging.debug('absolute path, where to extract asup: %s',
                              os.path.join(trafero_ccma_volume, working_dir, asup_dir))
                unpack_tgz(
                    os.path.join(trafero_ccma_volume, working_dir, asup_dir), tgz)

                # Trafero ingest: Upload data from ASUP to Trafero database
                logging.info('Ingest ASUP %s in Trafero...', tgz)
                new_cluster, new_node = ingest_into_trafero(
                    objects_counters_dict, working_dir + '/' + asup_dir, trafero_address, True)
                logging.debug('ingested cluster %s, node %s', new_cluster, new_node)

                if not cluster:
                    cluster, node = new_cluster, new_node
                elif (cluster, node) != (new_cluster, new_node):
                    logging.warning('Expected cluster %s and node %s, but found cluster %s and '
                                    'node %s. This means, you gave several ASUPs as input, which '
                                    'do not belong all to the same cluster and node. ASUP for '
                                    'cluster %s and node %s will be ignored.', cluster, node,
                                    new_cluster, new_node, new_cluster, new_node)

        else:
            logging.debug('Ingest type is "ccma"')

            logging.info('Copying all ccma files into Trafero\'s \'ccma\' volume...')
            copy_ccmas(input_data, os.path.join(trafero_ccma_volume, working_dir))

            logging.info('Ingest ccma files in Trafero...')
            cluster, node = ingest_into_trafero(
                objects_counters_dict, working_dir, trafero_address, False)
            logging.debug('ingested cluster %s, node %s', cluster, node)

        # check, if any ingestion was successful
        if not cluster and not node:
            logging.info('It seems like none of your input was ingested successfully. Hence,'
                         'can\'t retrieve any values. Quitting.')
            sys.exit(0)

        # Trafero retrieve values: Download data in json format from Trafero database
        logging.info('Retrieve values from Trafero...')
        retrieve_values(objects_counters_dict, cluster, node, trafero_address, output_dir)

        # Trafero delete: Remove ASUP from Trafero database
        logging.info('Delete ingested data from Trafero...')
        delete_from_trafero(cluster, node, trafero_address)

        logging.info('Done. You will find json files converted from your ASUP/ccma data under %s. '
                     'You can now pass this directory to PicDat.', output_dir)

    except requests.exceptions.ConnectionError:
        logging.error('Caught a ConnectionError. Seems like the Trafero container you '
                      'specified in your config.yml is not reachable.')
    finally:
        # remove ASUP from Trafero's 'ccma' volume
        shutil.rmtree(os.path.join(trafero_ccma_volume, working_dir))
        logging.info('(Deleted all files copied to Trafero\'s \'ccma\' volume)')


run_conversion()
