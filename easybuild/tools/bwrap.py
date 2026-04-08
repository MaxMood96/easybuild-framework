#!/usr/bin/env python
# #
# Copyright 2009-2026 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
# #
"""
Module for handling installations with bwrap (bubblewrap)

Authors:

* Samuel Moors (Vrije Universiteit Brussel)
"""
import json
import os

from easybuild.base import fancylogger
from easybuild.tools.build_log import print_msg
from easybuild.tools.config import install_path
from easybuild.tools.filetools import mkdir, write_file
from easybuild.tools.utilities import trace_msg

BWRAP_INFO = {
    'bwrap_cmd': [],
    'bwrap_eb_options': [],
    'bwrap_installpath': '',
    'installpath_modules': '',
    'installpath_software': '',
    'modules_to_install': set(),

}
BWRAP_INFO_JSON = 'bwrap_info.json'

_log = fancylogger.getLogger('bwrap', fname=False)


def prepare_bwrap(bwrap_installpath):
    """
    Prepare for running EasyBuild with bwrap:
    - update BWRAP_INFO
    - write json metadata file with BWRAP_INFO
    - set environment variable $EB_BWRAP_CMD

    :param bwrap_installpath: bwrap install path
    """

    BWRAP_INFO['bwrap_installpath'] = bwrap_installpath
    BWRAP_INFO['installpath_software'] = install_path(typ='software')
    BWRAP_INFO['installpath_modules'] = install_path(typ='modules')

    installpath_software = BWRAP_INFO['installpath_software']
    bwrap_modules_installpath = os.path.join(bwrap_installpath, 'modules')

    bwrap_cmd = ['bwrap', '--dev-bind', '/', '/']

    # bind mount all software directories
    for mod in BWRAP_INFO['modules_to_install']:
        installdir = os.path.join(os.path.realpath(installpath_software), mod)
        bwrap_installdir = os.path.join(bwrap_installpath, 'software', mod)
        mkdir(installdir, parents=True)
        mkdir(bwrap_installdir, parents=True)
        bwrap_cmd.extend(['--bind', bwrap_installdir, installdir])

    BWRAP_INFO['bwrap_cmd'] = bwrap_cmd

    # disable `--bwrap` to prepare for a real installation (in bwrap namespace)
    BWRAP_INFO['bwrap_eb_options'] = ['--disable-bwrap', f'--installpath-modules={bwrap_modules_installpath}']

    _log.info(f'Info needed for bwrap: {BWRAP_INFO}')

    # write json file with bwrap install info into bwrap installpath
    bwrap_infopath = os.path.join(BWRAP_INFO['bwrap_installpath'], BWRAP_INFO_JSON)
    write_file(bwrap_infopath, json.dumps(BWRAP_INFO, default=list, indent=2, sort_keys=True), backup=True)

    print_msg('Building/installing in bwrap namespace')
    trace_msg(f'bwrap command (to prefix eb command): {" ".join(BWRAP_INFO["bwrap_cmd"])}')
    trace_msg(f'bwrap info file: {bwrap_infopath}')
    trace_msg(f'bwrap EasyBuild options: {BWRAP_INFO["bwrap_eb_options"]}')

    # set environment variable $EB_BWRAP_CMD to make it available for the interactive debug shell
    # when rerunning with bwrap
    os.environ['EB_BWRAP_CMD'] = ' '.join(BWRAP_INFO['bwrap_cmd'])
