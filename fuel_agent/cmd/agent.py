#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import signal
import sys

from oslo_config import cfg
import six
import yaml

from fuel_agent import errors
from fuel_agent import manager as manager
from fuel_agent.openstack.common import log as logging
from fuel_agent import version

cli_opts = [
    cfg.StrOpt(
        'input_data_file',
        default='/tmp/provision.json',
        help='Input data file'
    ),
    cfg.StrOpt(
        'input_data',
        default='',
        help='Input data (json string)'
    ),
]

CONF = cfg.CONF
CONF.register_cli_opts(cli_opts)


def provision():
    main(['do_provisioning'])


def partition():
    main(['do_partitioning'])


def copyimage():
    main(['do_copyimage'])


def configdrive():
    main(['do_configdrive'])


def bootloader():
    main(['do_bootloader'])


def build_image():
    main(['do_build_image'])


def mkbootstrap():
    main(['do_mkbootstrap'])


def print_err(line):
    sys.stderr.write(six.text_type(line))
    sys.stderr.write('\n')


def handle_sigterm(signum, frame):
    # NOTE(agordeev): Since group pid of spawned subprocess is unknown,
    # fuel-agent needs to ignore SIGTERM sent by itself.
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    print_err('SIGTERM RECEIVED. Propagating it to subprocesses')
    os.killpg(os.getpid(), signal.SIGTERM)
    raise errors.UnexpectedProcessError(
        'Application was shut down gracefully')


def handle_exception(exc):
    LOG = logging.getLogger(__name__)
    LOG.exception(exc)
    print_err('Unexpected error')
    print_err(exc)
    sys.exit(-1)


def main(actions=None):
    # NOTE(agordeev): get its own process group by calling setpgrp.
    # Process group is used to distribute signals to subprocesses.
    # The main application is already a process group leader,
    # then there's no need to call os.setpgrp
    if os.getpid() != os.getpgrp():
        os.setpgrp()
    signal.signal(signal.SIGTERM, handle_sigterm)
    CONF(sys.argv[1:], project='fuel-agent',
         version=version.version_info.release_string())

    logging.setup('fuel-agent')
    LOG = logging.getLogger(__name__)

    try:
        if CONF.input_data:
            data = yaml.safe_load(CONF.input_data)
        else:
            with open(CONF.input_data_file) as f:
                data = yaml.safe_load(f)
        LOG.debug('Input data: %s', data)

        mgr = manager.Manager(data)
        if actions:
            for action in actions:
                getattr(mgr, action)()
    except Exception as exc:
        handle_exception(exc)


if __name__ == '__main__':
    main()
