class InvalidDataInputException(Exception):
    def __init__(self, data_filename):
        self.message = data_filename + ' not contains necessary information. ' \
                                       'Maybe it is no PerfStat output at all.'


class InstanceNameNotFoundException(Exception):
    def __init__(self, instance_name):
        self.message = 'Could not find a Name for this instance: ' + instance_name
