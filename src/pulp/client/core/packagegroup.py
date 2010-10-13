#!/usr/bin/python
#
# Pulp Registration and subscription module
# Copyright (c) 2010 Red Hat, Inc.
#
# Authors: Pradeep Kilambi <pkilambi@redhat.com>
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

import os
import sys
import time
from gettext import gettext as _

import pulp.client.constants as constants
from pulp.client.connection import (
    setup_connection, ConsumerConnection, RepoConnection)
from pulp.client.core.base import Action, Command
from pulp.client.core.utils import print_header, system_exit
from pulp.client.logutil import getLogger

# base package group action class ---------------------------------------------

_log = getLogger(__name__)

class PackageGroupAction(Action):

    def setup_connections(self):
        self.pconn = setup_connection(RepoConnection)
        self.cconn = setup_connection(ConsumerConnection)

    def setup_parser(self):
        self.parser.add_option("--id", dest="id",
                               help=_("package group id (required)"))

# package group actions -------------------------------------------------------

class List(PackageGroupAction):

    description = _('list available package groups')

    def setup_parser(self):
        self.parser.add_option("-r", "--repoid", dest="repoid",
                               help=_("repository label (required)"))

    def run(self):
        repoid = self.get_required_option('repoid')
        groups = self.pconn.packagegroups(repoid)
        if not groups:
            system_exit(os.EX_DATAERR,
                        _("No package groups found in repo [%s]") % (repoid))
        print_header(_("Repository: %s") % (repoid), _("Package Group Information"))
        for key in sorted(groups.keys()):
            print "\t %s" % (key)


class Info(PackageGroupAction):

    description = _('lookup information for a package group')

    def setup_parser(self):
        super(Info, self).setup_parser()
        self.parser.add_option("-r", "--repoid", dest="repoid",
                               help=_("repository label (required)"))

    def run(self):
        groupid = self.get_required_option('id')
        repoid = self.get_required_option('repoid')
        groups = self.pconn.packagegroups(repoid)
        if groupid not in groups:
            system_exit(os.EX_DATAERR,
                        _("Package group [%s] not found in repo [%s]") %
                        (groupid, repoid))
        print_header(_("Package Group Information"))
        info = groups[groupid]
        print constants.PACKAGE_GROUP_INFO % (
                info["name"], info["id"], info["mandatory_package_names"],
                info["default_package_names"], info["optional_package_names"],
                info["conditional_package_names"])


class Create(PackageGroupAction):

    description = _('create a package group')

    def setup_parser(self):
        super(Create, self).setup_parser()
        self.parser.add_option("-r", "--repoid", dest="repoid",
                               help=_("repository label (required)"))
        self.parser.add_option("-n", "--name", dest="name",
                               help=_("group name (required)"))
        self.parser.add_option("-d", "--description", dest="description", default="",
                               help=_("group description, default is ''"))

    def run(self):
        repoid = self.get_required_option('repoid')
        groupid = self.get_required_option('id')
        groupname = self.get_required_option('name')
        description = self.opts.description
        self.pconn.create_packagegroup(repoid, groupid, groupname, description)
        print _("Package group [%s] created in repository [%s]") % \
                (groupid, repoid)


class Delete(PackageGroupAction):

    description = _('delete a package group')

    def setup_parser(self):
        super(Delete, self).setup_parser()
        self.parser.add_option("-r", "--repoid", dest="repoid",
                               help=_("repository label (required)"))

    def run(self):
        repoid = self.get_required_option('repoid')
        groupid = self.get_required_option('id')
        try:
            self.pconn.delete_packagegroup(repoid, groupid)
        except Exception, e:
            _log.error(e)
            print _("Unable to delete Packagegroup [%s] from repository [%s]") % \
                (groupid, repoid)
        else:
            print _("Packagegroup [%s] deleted from repository [%s]") % \
                (groupid, repoid)


class AddPackage(PackageGroupAction):

    description = _('add package to an existing package group')

    def setup_parser(self):
        super(AddPackage, self).setup_parser()
        self.parser.add_option("-r", "--repoid", dest="repoid",
                               help=_("repository label (required)"))
        self.parser.add_option("-n", "--name", action="append", dest="name",
                               help=_("packages to be added; to specify multiple packages use multiple -n (required)"))
        self.parser.add_option("-t", "--type", dest="grouptype", default="default",
                               help=_("type of list to add package to, example 'mandatory', 'optional', 'default', 'conditional'"))
        self.parser.add_option("--requires", dest="requires", default=None,
                               help=_("required package name, only used by 'conditional' package group type"))

    def run(self):
        repoid = self.get_required_option('repoid')
        pnames = self.get_required_option('name')
        groupid = self.get_required_option('id')
        grouptype = self.opts.grouptype
        requires = None # Only used by conditional group type
        supported_types = ["mandatory", "optional", "default", "conditional"]
        if grouptype not in supported_types:
            system_exit(1, 
                    _("Bad package group type [%s].  Supported types are: %s" % \
                        (grouptype, supported_types)))
        if grouptype == "conditional":
            requires = self.get_required_option("requires")

        self.pconn.add_packages_to_group(repoid, groupid, pnames, grouptype, requires)
        if grouptype == "conditional":
            print _("Following packages added to group [%s] in repository [%s] for required package [%s]: \n %s") % \
                (groupid, repoid, requires, pnames)
        else:
            print _("Following packages added to group [%s] in repository [%s]: \n %s") % \
                (groupid, repoid, pnames)


class DeletePackage(PackageGroupAction):

    description = _('delete package from an existing package group')

    def setup_parser(self):
        super(DeletePackage, self).setup_parser()
        self.parser.add_option("-r", "--repoid", dest="repoid",
                               help=_("repository label (required)"))
        self.parser.add_option("-n", "--name", dest="name",
                               help=_("package name (required)"))
        self.parser.add_option("-t", "--type", dest="grouptype", default='default',
                               help=_("type of list to delete package from, example 'mandatory', 'optional', 'default'"))
        self.parser.add_option("--requires", dest="requires", default=None,
                               help=_("required package name, only used by 'conditional' package group type"))

    def run(self):
        repoid = self.get_required_option('repoid')
        pkgname = self.get_required_option('name')
        groupid = self.get_required_option('id')
        grouptype = self.opts.grouptype
        requires = None # Only used by conditional group type
        if grouptype == "conditional":
            requires = self.get_required_option("requires")
        try:
            self.pconn.delete_package_from_group(repoid, groupid, pkgname, grouptype, requires)
        except Exception, e:
            _log.error(e)
            print _("Unable to delete [%s] from group [%s] in repository [%s]") % \
                    (pkgname, groupid, repoid)
        else:
            print _("Package [%s] deleted from group [%s] in repository [%s]") % \
                    (pkgname, groupid, repoid)


class Install(PackageGroupAction):

    description = _('schedule a packagegroup install')

    def setup_parser(self):
        self.parser.add_option("-g", "--pkggroupid", action="append", dest="pkggroupid",
                               help=_("packagegroup to install on a given consumer; to specify multiple package groups use multiple -g (required)"))
        self.parser.add_option("--consumerid", dest="consumerid",
                               help=_("consumer id (required)"))

    def run(self):
        consumerid = self.get_required_option('consumerid')
        pkggroupid = self.get_required_option('id')
        task = self.cconn.installpackagegroups(consumerid, pkggroupid)
        print _('Created task id: %s') % task['id']
        state = None
        spath = task['status_path']
        while state not in ('finished', 'error', 'canceled', 'timed_out'):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(2)
            status = self.cconn.task_status(spath)
            state = status['state']
        if state == 'finished':
            print _('\n[%s] installed on %s') % (status['result'], consumerid)
        else:
            print("\nPackage group install failed")

# package group command -------------------------------------------------------

class PackageGroup(Command):

    description = _('package group specific actions to pulp server')
