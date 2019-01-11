#! /usr/bin/python
"""
STANDALONERUN is the usual entry point into BCore psychophysics functionality.

StandAloneRun
     -s, --subject    subject_id
     --server-path    server path to BServer
     -p, --protocol   protocol name. See ../User folder for example protocols
     -r, --reward     reward amount in ms
     -p, --punishment punishment timeout in ms
"""
import sys
import os
from BCore import get_base_directory, get_ip_addr
from BCore.Classes.ClientAndServer.BServer import BServerLocal
from BCore.Classes.Protocol import Protocol, DemoGratingsProtocol
from BCore.Classes.Subject import DefaultVirtual
from BCore.Classes.Station import StandardVisionBehaviorStation,StandardKeyboardStation,StandardVisionHeadfixStation

# User specific protocols
from BCore.Users.Biogen.PhysiologyProtocols import get_phys_protocol_biogen
from BCore.Users.Biogen.BehaviorProtocols import get_behavior_protocol_biogen
from BCore.Users.Biogen import get_protocol_from_name

__author__ = "Balaji Sriram"
__version__ = "0.0.1"
__copyright__ = "Copyright 2018"
__license__ = "GPL"
__maintainer__ = "Balaji Sriram"
__email__ = "balajisriram@gmail.com"
__status__ = "Production"

SERVER_PORT = 12345

def load_bserver(path, subject_id):
    if not os.path.exists(path):
        print("STANDALONERUN:LOAD_BSERVER:Server not found at location. Creating new server by default.")
        b_server = BServerLocal()
        b_server._setup_paths()
        b_server.save()
    else:
        b_server = BServerLocal.load_server(path)  # load the server from path


    if subject_id not in b_server.get_subject_ids():
        print("STANDALONERUN:LOAD_BSERVER:Subject %r wasn''t found in server. Adding...\n" % subject_id)
        sub = DefaultVirtual(subject_id=subject_id,reward=20.,timeout=1000.)
        b_server.add_subject(sub)
    else:
        print("STANDALONERUN:LOAD_BSERVER:Subject {0} was found in server\n".format(subject_id))

    if not b_server.get_station_ids():
        print("STANDALONERUN:LOAD_BSERVER:No Stations found in server. Creating new station...\n")
        stn  = StandardVisionHeadfixStation(sound_on=True, station_id=0, station_location=(0, 0, 0))
        b_server.add_station(stn)
    elif len(b_server.get_station_ids())>1:
        RuntimeError('STANDALONERUN:LOAD_BSERVER:too many stations for server')
    else:
        print("STANDALONERUN:LOAD_BSERVER:Will run on station %r" % b_server.get_station_ids())

    return b_server



def stand_alone_run(subject_id = 'demo1', bserver_path = None, protocol = None, reward = None, punishment = None):
    # look for local server and collect information about the Subject being run
    if not bserver_path:bserver_path = BServerLocal.get_standard_server_path()

    b_server = load_bserver(bserver_path, subject_id)

    # add subject to station
    stn = b_server.stations[0]

    subjects = b_server.get_subject_ids()
    found = False
    for i,subj in enumerate(subjects):
        if subj==subject_id:
            found = True
            sub = b_server.subjects[i]
            break

    # deal with subject protocol
    if not sub.protocol:
        # if i gave a protocol name, add that
        if protocol:
            protocol_name_requested = protocol
            protocol_requested = get_protocol_from_name(protocol_name_requested) # requested protocol
            sub.add_protocol(protocol_requested)
        # else add the demo protocol
        else:
            sub.add_protocol(DemoGratingsProtocol())
    else:
        if protocol:
            protocol_name_requested = protocol
            protocol_requested = get_protocol_from_name(protocol_name_requested) # requested protocol
            if sub.protocol.name==protocol_requested.name:
                pass
            else:
                sub.replace_protocol(protocol_requested)
    stn._stand_alone = True
    stn.add_subject(sub)


    print("STANDALONERUN:STAND_ALONE_RUN:Running on Protocol "+stn.subject.protocol.name)
    # run do_trials on station
    stn.do_trials()
    # clean up at end of trials
    stn.remove_subject(sub)


if __name__ == '__main__':
    # set defaults for all the things that need to be sent to the bootstrap
    # function

    subject_id = 'demo1'
    bserver_path = None
    protocol = None
    reward = None
    punishment = None

    # parse input arguments and send to bootstrap
    # loop through the arguments and deal with them one at a time
    args = iter(sys.argv)
    added = False

    for arg in args:
        if arg in ['subject_id','--subject','-s']:
            subject_id = next(args)
            which_added = 'subject_id'
            added = True
        elif arg in ['bserver_path','--server-path']:
            bserver_path = next(args)
            which_added = 'bserver_path'
            added = True
        elif arg in ['protocol','--protocol','-p']:
            protocol = next(args)
            which_added = 'protocol'
            added = True
        elif arg in ['reward','--reward','-r']:
            reward = next(args)
            which_added = 'reward'
            added = True
        elif arg in ['punishment','--punishment','-p']:
            punishment = next(args)
            which_added = 'punishment'
            added = True
        if added:
            print('added ::',which_added)
            added = False
    print('running stand_alone on subject:{0},path:{1},protocol:{2}'.format(subject_id,bserver_path,protocol))
    stand_alone_run(subject_id=subject_id, bserver_path=bserver_path, protocol=protocol,reward=reward,punishment=punishment)
