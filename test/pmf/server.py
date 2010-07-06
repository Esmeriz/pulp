#! /usr/bin/env python
#
# Copyright (c) 2010 Red Hat, Inc.
#
# Authors: Jeff Ortel <jortel@redhat.com>
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

import sys
sys.path.append('../../')

from pmf.mode import Mode
from pmf.proxy import Proxy
from pmf.base import AgentProxy as Base
from pmf.producer import RequestProducer


class RepoLib(Proxy):
    pass

class Dog(Proxy):
    pass


class Agent(Base):

    def __init__(self, consumerid):
        producer = RequestProducer()
        self.repolib = RepoLib(consumerid, producer)
        self.dog = Dog(consumerid, producer)
        Base.__init__(self, producer)


def demo(agent):

    print agent.dog.bark('hello')
    print agent.dog.wag(3, __mode=Mode(0, 'task'))
    print agent.dog.bark('hello')
    print agent.repolib.update()

    try:
        print agent.repolib.updated()
    except Exception, e:
        print repr(e)

    try:
        print agent.dog.notpermitted()
    except Exception, e:
        print repr(e)


if __name__ == '__main__':
    agent = Agent('123')
    demo(agent)
    agent.close()