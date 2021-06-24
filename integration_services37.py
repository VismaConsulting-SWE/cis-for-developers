
# !/usr/bin/python3
# -*- coding: utf-8 -*-
# [ Component | Integration Services Mockup
#   Can be used as a task replacement to test a python component
# ]
# [ Property | Connectable=0 | Not connectable ]
#

import os
import tempfile
import re
import sys
import shutil
import time
import logging
import logging.handlers
import collections
import copy
import atexit
from collections import deque

cis_version = '2.7.0.0'
mock = True
quit = False
mock = True
quit = False

log = logging.getLogger(__name__)

re_info = RE_INFO = 0
re_normal = RE_NORMAL = 1
re_error = RE_ERROR = 2
re_system = RE_SYSTEM = 3
re_warning = RE_WARNING = 4

rd_info = RD_INFO = 0
rd_normal = RD_NORMAL = 1
rd_error = RD_ERROR = 2
rd_system = RD_SYSTEM = 3
rd_warning = RD_WARNING = 4

rl_normal = RL_NORMAL = 1
rl_error = RL_ERROR = 2
rl_complete = RL_COMPLETE = 3
rl_marked_complete = RL_MARKED_COMPLETE = 4

ss_undefined = SS_UNDEFINED = 0
ss_active = SS_ACTIVE = 1
ss_inactive = SS_INACTIVE = 2
ss_error = SS_ERROR = 3
ss_error_end = SS_ERROR_END = 4
ss_remove_error = SS_REMOVE_ERROR = 5
ss_remove = SS_REMOVE = 6
ss_pending = SS_PENDING = 7
ss_complete = SS_COMPLETE = 8
ss_marked_complete = SS_MARKED_COMPLETE = 9

indentifiers = {}
module_locations = {}
module_tempdirectory = None
global_task = None


def __cleanup():
    if module_tempdirectory and os.path.exists(module_tempdirectory):
        shutil.rmtree(module_tempdirectory)


atexit.register(__cleanup)


def new_task(name='Mockup', modules_to_log=None, calling_module=None):
    return Task(name, modules_to_log, calling_module=calling_module)


def get_version():
    return cis_version

def run_component(component):
    c = remote_import(component)
    c.main(global_task)

def remote_import(name):
    remote_get(name)

    name = name.replace('.py', '')
    return __import__(name)


def remote_get(name):
    if name in module_locations:
        location = module_locations[name]

        if '~' in location:
            location = os.path.expanduser(location)

        if not os.path.exists(location):
            raise Exception(
                "remote_get failed. Cannot find '{}' in location '{}'".format(
                    name, location))

        module_tempdirectory = tempfile.mkdtemp()
        shutil.copytree(location, os.path.join(module_tempdirectory,
                                               name))

        sys.path.insert(0, module_tempdirectory)


def get_original_task():
    return Task()


def get_local_private_key():
    return ''


def get_local_certificate():
    return ''


def get_remote_certificate(workspaceid):
    return ''


class CisLogFilter(logging.Filter):

    def __init__(self, modules):
        logging.Filter.__init__(self)
        self.modules = modules

    def filter(self, record):
        if self.modules:
            for module in self.modules:
                if re.match(module, record.name) \
                        and int(self.modules[module]) \
                        <= int(record.levelno):
                    return True
        return False


class MandatoryParameterMissing(Exception):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Mandatory parameter '{}' missing.".format(self.name)


class Task:

    def __init__(
            self,
            name=None,
            modules_to_log=None,
            calling_module=None):

        modules = {'root': logging.INFO, __name__: logging.INFO,
                   '__main__': logging.INFO}

        self.task_name = name

        if modules_to_log:
            modules.update(modules_to_log)

        self.task_id = '#FAKE'
        self.flags = 0
        self.parameters = collections.OrderedDict()
        self.data_deque = deque()
        self.datafiles = deque()
        self.data_file = None
        self.tempfiles = []
        self.components = []

        self.file_identifier = ''
        self.status = SS_ACTIVE
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        formatter = \
            logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        ch.setLevel(logging.DEBUG)

        ch.setFormatter(formatter)
        ch.addFilter(CisLogFilter(modules))

        for h in self.log.handlers:
            if isinstance(h, logging.StreamHandler):
                self.log.removeHandler(h)

        self.log.addHandler(ch)

        calling_module_logger = logging.getLogger(calling_module)

        for h in calling_module_logger.handlers:
            if isinstance(h, logging.StreamHandler):
                calling_module_logger.removeHandler(h)

        calling_module_logger.addHandler(ch)

        self._set_initial_parameters()

        self.events = {
            RE_INFO: [],
            RE_NORMAL: [],
            RE_ERROR: [],
            RE_SYSTEM: [],
            RE_WARNING: [],
        }

        self.quit_and_restart_count = 0

    def __del__(self):
        for (f, delete) in self.tempfiles:
            if delete:
                try:
                    os.remove(f)
                    log.debug("'{}' removed.".format(f))
                except Exception as e:
                    log.warning(e)

        for f in self.datafiles:
            try:
                os.remove(f)
            except Exception as e:
                log.warning(e)

    #
    # internal
    #

    def _set_initial_parameters(self):
        self.parameters['ActivatedByPID'] = str(os.getpid())
        self.parameters['ActivatedBy'] = 'MockCIS'
        self.parameters['WorkspaceId'] = \
            'internal:cis-mockcustomer-mockservice-trunk/default'

    def _is_status_active(self):
        if (self.status == SS_ACTIVE or
                self.status == SS_PENDING or
                self.status == SS_ERROR):
            return True
        else:
            return False

    def _is_status_error(self):
        if (self.status == SS_ERROR or self.status == SS_ERROR_END):
            return True
        else:
            return False

    def _get_parameter(
            self,
            key,
            default='',
            required=False,
            hidden=False,
            protected=False,
            to_boolean=False,
            to_numeric=False):

        if not key.lstrip('-+?#') in self.parameters:
            if re.search('^[-?]*\+', key) or required:
                raise MandatoryParameterMissing(key)
            else:
                value = default
        else:
            value = self.parameters[key.lstrip('-+?#')]

        if re.search('%[^%]+%', key):
            nested_parameter_name = key.partition('%')[2].rpartition('%')[0]
            self.log.debug("calling self.get_parameter('{}', '{}')".format(
                nested_parameter_name, default))

            value = self._get_parameter(
                nested_parameter_name,
                default,
                required,
                hidden,
                protected,
                to_boolean,
                to_numeric)

        if (value and isinstance(value, str) and
                re.search('%[^%]+%', value)):
            nested_parameter_name = \
                value.partition('%')[2].rpartition('%')[0]
            value = value.replace(
                '%' + nested_parameter_name + '%',
                self._get_parameter(
                    nested_parameter_name, default, required))

        if not value and required:
            raise MandatoryParameterMissing(key)

        if to_boolean or re.search("^[-+#]*\?.*$", key):
            if (isinstance(value, basestring) and
                    re.search('^(yes|true|ja|y|j|1)$', value.lower())):
                value = 1
            else:

                # Else return 0 if not value is a numeric then return 1

                try:
                    value = int(value)
                    if value > 0:
                        value = 1
                    else:
                        value = 0
                except BaseException:
                    value = 0

        if ((to_numeric or re.search('^[-+?]*#.*$', key)) and
                isinstance(value, str)):
            try:
                value = int(value)
            except BaseException:
                value = 0

        return value

    def _get_sub_parameter(
            self,
            name,
            key,
            default='',
            required=False,
            to_boolean=False,
            to_numeric=False):

        if re.search('=', name):
            param = name
        else:
            param = self._get_parameter(
                name,
                default='',
                required=required,
                to_boolean=to_boolean,
                to_numeric=to_numeric)

        value = ''
        if default:
            value = default

        for sub_parameter in param.split('|'):
            if sub_parameter.startswith('{'):
                continue
            p = sub_parameter.split('=', 2)
            if p[0] == key:
                value = p[1]
                break

        if not value and required:
            raise MandatoryParameterMissing(key)

        return value

    #
    # public helper methods
    #

    def add_mock_component(
            self,
            identifier,
            wid,
            component):

        self.mock_components['{}@{}'.format(identifier, wid)] = \
            component

    def add_mock_component(self, task_id, component):
        self.mock_components['{}'.format(task_id)] = component

    def set_config_parameter(self, name, value):
        self.log.debug("set_config_parameter('{}', '{}')".format(
            name, value))

        config_index = self._get_parameter('CurrentConfig', '1')
        config = self._get_parameter('Config' + config_index, None)
        p = collections.OrderedDict()
        if config:
            for (k, v) in [i.split('=', 2) for i in config.split('|')]:
                p[k] = v

        p[name] = value

        self.parameters['Config' + config_index] = \
            '|'.join(['{}={}'.format(k, v) for (k, v) in p.iteritems()])

    def set_config(self, index, config):
        self.log.debug("set_config({}, '{}')".format(index, config))
        self.parameters['Config' + index] = config

    def set_current_config_index(self, index):
        self.log.debug('set_current_config_index({})'.format(index))
        self.parameters['CurrentConfig'] = index

    def set_file_identifier(self, identifier):
        self.log.debug("set_file_identifier('{}')".format(identifier))
        self.file_identifier = identifier

    #
    # public task methods
    #

    def activate(self, report_to_log=True, check_limit=True):

        attached_wid = self.get_parameter('WorkspaceId')

        self.set_status(ss_active)
        return True

    def attach_id(self, id):
        self.log.debug("attach_id('{}')".format(id))

        if id in identifiers:
            self.parameters.update(identifiers[id])
            return True

        self.log.debug("""Mockup task cannot be attached
            (must be added with add_mock_component)"""
                       )
        return False

    def attach_integration(self, identifier, wid=None):
        self.attached_type = 'integration'
        self.attached_identifier = identifier
        self.set_parameter('WorkspaceId', wid)
        self.set_parameter('IntegrationName', identifier)
        self.log.debug("attach_{}('{}', '{}')".format(self.attached_type,
                                                      identifier, wid))

        identifier = '{}_{}'.format(wid, identifier)

        log.debug(identifiers)
        log.debug(identifier)

        if identifier in identifiers:
            self.parameters.update(identifiers[identifier])
            return True

        return False

    def attach_process(self, identifier, wid=None):
        self.attached_type = 'process'
        self.attached_identifier = identifier
        self.set_parameter('WorkspaceId', wid)
        self.log.debug("attach_{}('{}', '{}')".format(type, identifier,
                                                      wid))

        component = '{}@{}'.format(identifier, wid)

        if component in self.mock_components:
            self.mock_component = self.mock_components[component]
            return True

        self.log.debug("""Mockup task cannot be attached
            (must be added with add_mock_component)"""
                       )
        return False

    def attach_task(self, identifier, wid=None):
        self.attached_type = 'task'
        self.attached_identifier = identifier
        self.set_parameter('WorkspaceId', wid)
        self.log.debug("attach_{}('{}', '{}')".format(type, identifier,
                                                      wid))

        component = '{}@{}'.format(identifier, wid)

        if component in self.mock_components:
            self.mock_component = self.mock_components[component]
            return True

        self.log.debug("""Mockup task cannot be attached
            (must be added with add_mock_component)"""
                       )
        return False

    def attach_trigger(self, identifier, wid=None):
        self.attached_type = 'trigger'
        self.attached_identifier = identifier
        self.set_parameter('WorkspaceId', wid)
        self.log.debug("attach_{}('{}', '{}')".format(type, identifier,
                                                      wid))

        component = '{}@{}'.format(identifier, wid)

        if component in self.mock_components:
            self.mock_component = self.mock_components[component]
            return True

        self.log.debug("""Mockup task cannot be attached
            (must be added with add_mock_component)"""
                       )
        return False

    def continue_run(self):
        self.log.debug('continue_run() = {}'.format(self._is_status_active()))
        return self._is_status_active()

    def create_temp_file(self, extension=None, auto_delete=True):
        if extension:
            extension = '.{}'.format(extension)

        temp_file = \
            tempfile.NamedTemporaryFile(suffix='{}'.format(extension))
        temp_file = temp_file.name
        open(temp_file, 'w').close()

        self.tempfiles.append((temp_file, auto_delete))
        self.log.debug('create_temp_file() = {}'.format(temp_file))
        return temp_file

    def delete_all_parameters(self):
        self.log.debug('delete_all_parameters()')
        self.parameters = {}

    def delete_parameter(self, key):
        self.log.debug("delete_parameter('{}')".format(key))
        try:
            del self.parameters[key]
        except BaseException:
            pass

    def delete_temp_files(self, extension='*', include_hidden=False):
        self.log.debug('delete_temp_files()')
        for (f, delete) in self.tempfiles:
            if delete:
                try:
                    os.remove(file)
                except Exception as e:
                    log.warning(e)

    def get_activated_by(self):
        activated_by = ''
        if 'ActivatedBy' in self.parameters:
            activated_by = self.parameters['ActivatedBy']
        self.log.debug('get_activated_by() = {}'.format(activated_by))
        return activated_by

    def get_config_parameter(
            self,
            key,
            default='',
            required=False,
            to_boolean=False,
            to_numeric=False):

        config_index = self._get_parameter('CurrentConfig', '1')
        value = self._get_sub_parameter(
            'Config' + config_index,
            key,
            default,
            required,
            to_boolean,
            to_numeric)
        self.log.debug("get_config_parameter('{}') = {}".format(key,
                                                                value))
        return value

    def get_data(self):
        value = ''
        if len(self.data_deque) > 0:
            value = self.data_deque.popleft()
        self.log.debug('get_data() = {}'.format(value))
        return value

    def get_data_file(self):
        datafile = self.datafiles.popleft()
        self.log.debug('get_data_file() = {}'.format(datafile))
        return datafile

    def get_file_identifier(self, filename):
        self.log.debug("get_file_identifier('{}') = {}".format(filename,
                                                               self.file_identifier))

        return self.file_identifier

    def get_flags(self):
        self.log.debug('get_flags() = {}'.format(self.flags))
        return self.flags

    def get_id(self):
        self.log.debug('get_id() = {}'.format(self.task_id))
        return self.task_id

    def get_input_file(self, quit_if_missing=True):
        input_file = self._get_parameter(
            'InputFile', required=quit_if_missing)
        self.log.debug('get_input_file() = {}'.format(input_file))
        return input_file

    def get_name(self):
        task_type = self._get_parameter('TaskType')
        task_name = self._get_parameter('{}Name'.format(task_type))
        if task_name == '':
            task_name = self.task_name
        self.log.debug('get_name() = {}'.format(task_name))
        return task_name

    def get_owner(self):
        owner = self._get_parameter('Owner')
        self.log.debug('get_owner() = {}'.format(owner))
        return owner

    def get_parameter(
            self,
            key,
            default='',
            required=False,
            hidden=False,
            protected=False,
            to_boolean=False,
            to_numeric=False):

        value = self._get_parameter(
            key,
            default,
            required,
            hidden,
            protected,
            to_boolean,
            to_numeric)

        self.log.debug("get_parameter('{}') = {}".format(key, value))

        return value

    def get_parameters(self, to_dictionary=False):
        if to_dictionary:
            params = {}

            for (key, value) in self.parameters.items():
                params[key] = value
            return params
        else:
            return '%'.join(['{}={}'.format(k, v) for (k, v) in
                             self.parameters.items()])

    def get_status(self):
        self.log.debug('get_status() = {}'.format(self.status))
        return self.status

    def get_sub_parameter(
            self,
            param,
            key,
            default='',
            required=False,
            to_boolean=False,
            to_numeric=False):

        value = self._get_sub_parameter(
            param,
            key,
            default,
            required,
            to_boolean,
            to_numeric)

        self.log.debug("get_sub_parameter('{}', '{}') = {}".format(
            param, key, value))

        return value

    def get_workspace_id(self):
        workspace_id = _get_parameter('WorkspaceId')
        self.log.debug('get_workspace_id() = {}'.format(workspace_id))
        return workspace_id

    def is_active(self):
        return self._is_status_active()

    def is_test_mode(self):
        return self._get_parameter('?TestMode', '0')

    def load(self):
        self.log.debug('load()')

    def new_task(self):
        task = Task()
        task.parameters = copy.deepcopy(self.parameters)
        return task

    def quit(self):
        self.log.debug('quit()')
        if self._is_status_error():
            self.status = SS_ERROR_END
        else:
            self.status = SS_INACTIVE
        quit = True

    def quit_and_restart(self, max_restart=1, sleep_seconds=60):
        self.log.debug('quit_and_restart()')
        if self._is_status_error():
            self.status = SS_ERROR_END
        else:
            self.status = SS_INACTIVE

        self.quit_and_restart_count += 1
        quit = True

    def remove(self):
        self.log.debug('remove()')

    def report_debug(self, type=RD_NORMAL, text=''):
        if isinstance(text, Exception):
            log.exception(text)
        else:
            eventRow = '{}'.format(text)

            if type == RD_INFO:
                log.info(eventRow)
            elif type == RD_NORMAL:
                log.info(eventRow)
            elif type == RD_SYSTEM:
                log.info(eventRow)
            elif type == RD_WARNING:
                log.warning(eventRow)
            elif type == re_error:
                log.error(eventRow)
            else:
                raise TypeError('Invalid argument to report_debug')

    def report_event(self, type=RE_NORMAL, text=''):
        self.events[type].append(text)

        if isinstance(text, Exception):
            log.exception(text)
        else:
            eventRow = '{}'.format(text)

            if type == RE_INFO:
                log.info(eventRow)
            elif type == RE_NORMAL:
                log.info(eventRow)
            elif type == RE_SYSTEM:
                log.info(eventRow)
            elif type == RE_WARNING:
                log.warning(eventRow)
            elif type == RE_ERROR:
                self.status = SS_ERROR
                self.set_parameter('LastErrorText', text)
                log.error(eventRow)
            else:
                raise TypeError('Invalid argument to report_event')

    def report_log(self, type=RL_NORMAL, text=''):
        depth = 0
        log_entry = ''

        for log_part in text.split('|'):
            if depth == 0:
                log_entry = '{}'.format(log_part)
                depth += 1
            else:
                if re.search('=', log_part):
                    log_entry = log_entry + '\n{}{}'.format(
                        depth * '\t', log_part)
                else:
                    if log_part == '':
                        log_part = '<component>'
                    log_entry = log_entry + '\n{}{}'.format(
                        depth * '\t', log_part)
                    depth += 1

        if type == RL_NORMAL:
            log.info(log_entry)
        elif type == RL_ERROR:
            self.status = SS_ERROR
            self._set_parameter('LastErrorText', text)
            log.error(log_entry)
        elif type == RL_COMPLETE:
            log.info('RL_COMPLETE: ' + log_entry)
        elif type == RL_MARKED_COMPLETE:
            log.info('RL_MARKED_COMPLETE: ' + log_entry)
        else:
            raise TypeError('Invalid argument to report_log')

    def set_data(self, item):
        self.log.debug("set_data('{}')".format(item))
        self.data_deque.append(item)

    def set_data_file(self, item):
        datafile = self.create_temp_file('data')
        shutil.copyfile(item, datafile)

        self.log.debug("set_data_file('{}') => datafiles.append('{}')".format(
            item, datafile))

        self.datafiles.append(datafile)

    def set_flags(self, flags):
        self.log.debug('set_flags({})'.format(flags))
        self.flags = flags

    def set_id(self, task_id):
        self.log.debug('set_task_id({})'.format(task_id))
        self.task_id = task_id

    def set_input_file(self, file_name, original_name=None):
        self.log.debug("set_input_file('{}')".format(file_name))
        self.parameters['InputFile'] = file_name
        if original_name:
            self.parameters['OriginalName'] = original_name
        else:
            self.parameters['OriginalName'] = \
                os.path.split(file_name)[1]

    def set_owner(self, owner):
        self.log.debug('set_owner({})'.format(owner))
        self.parameters['Owner'] = owner

    def set_parameter(self, name, value):
        self.log.debug("set_parameter('{}', '{}')".format(name, value))
        self.parameters[name] = value

    def set_status(self, cis_status):
        self.log.debug('set_status({})'.format(cis_status))
        self.status = cis_status

    def sleep(self, seconds):
        self.log.debug('sleep() = {}, seconds, press Ctrl+Del to break'.format(
            seconds))

        while seconds > 0:
            seconds -= 1
            time.sleep(1)
            if not self._is_status_active():
                break

    def store():
        self.log.debug('store()')
