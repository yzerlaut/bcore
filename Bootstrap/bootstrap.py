import sys

from BCore.Classes.Stations.StandardVisionBehaviorStation \
    import StandardVisionBehaviorStation
from BCore.Classes.Stations.Station \
    import Station


def bootstrap(mode='init', procType='client', **kwargs):
    if mode == 'init':
        if procType == 'client':
            st = Station(**kwargs)
            st.run()
        elif procType == 'standardVisionClient' or procType == 'std-cli':
            st = StandardVisionBehaviorStation(**kwargs)
            st.run()
        elif procType == 'server':
            pass
        elif procType == 'localServer':
            pass
    elif mode == 'run':
        if procType == 'client':
            pass
        elif procType == 'standardVisionClient' or procType == 'std-cli':
            st = StandardVisionBehaviorStation(**kwargs)
            st.run()
        elif procType == 'server':
            pass
        elif procType == 'localServer':
            pass
        st = StandardVisionBehaviorStation()
    else:
        raise NotImplementedError('Unknown bootstrap mode:: \
            You sent %s. Allowed {''init'',''run''}')


if __name__ == '__main__':
    # set defaults for all the things that need to be sent to the bootstrap
    # function
    mode = 'init'
    procType = 'client'
    bootstrapKWArgs = {
        'stationID': 0,
        'stationName': 'Station0',
        'display': None,
        'soundOn': False,
        'parallelPort': 'standardVisionBehaviorDefault',
        'serverID': 0,
        'serverName': 'Server0'
        }
    # parse input arguments and send to bootstrap
    # loop through the arguments and deal with them one at a time
    args = iter(sys.argv)
    for arg in args:
        if arg == 'bootstrap':
            # do nothing. this is the initial call to python
            pass
        elif arg == 'mode' or arg == '-mode' or arg == '--mode':
            arg = next(args)
            mode = arg
        elif arg == 'procType':
            arg = next(args)
            procType = arg
        elif (arg == 'stationID') or (  # all the integers
            arg == 'serverID'):
            bootstrapKWArgs[arg] = int(next(args))
        elif (arg == 'stationName') or (  # all the strings
            arg == 'display') or (
            arg == 'parallelPort') or (
            arg == 'serverName'):
            bootstrapKWArgs[arg] = next(args)
        elif (arg == 'soundOn'):  # all the bools
            bootstrapKWArgs[arg] = next(args)

    bootstrap(mode, procType, **bootstrapKWArgs)