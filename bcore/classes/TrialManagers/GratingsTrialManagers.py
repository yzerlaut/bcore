from verlib import NormalizedVersion as Ver
import bcore.classes.TrialManagers.PhaseSpec as ps
import bcore.classes.TrialManagers.BaseTrialManagers as btm
import bcore.classes.ReinforcementManager as reinfmgr
import bcore.classes.Station as st
import psychopy
import random
import numpy as np
import psychopy.visual,psychopy.core
from psychopy.constants import (STARTED, PLAYING, PAUSED, FINISHED, STOPPED, NOT_STARTED, FOREVER)

__author__ = "Balaji Sriram"
__version__ = "0.0.1"
__copyright__ = "Copyright 2018"
__license__ = "GPL"
__maintainer__ = "Balaji Sriram"
__email__ = "balajisriram@gmail.com"
__status__ = "Production"

"""
    TODOs:
    1. All Ver should be inside the init - Keeping it outside make them irrelevant
    2. Figure out a way to send subject into _setup_phases. Need it for reward and timeout values
"""
##########################################################################################
##########################################################################################
######################### GRATINGS TRIAL MANAGERS - SHOWS ################################
############################# ONE GRATING AT A TIME ######################################
##########################################################################################
##########################################################################################

class Gratings(btm.BaseTrialManager):
    """
        GRATINGS defines a standard gratings trial manager
            deg_per_cycs
            orientations
            drift_frequencies
            phases
            contrasts
            durations
            radii

    """
    _Cached_Stimuli = None
    _compiler = None

    def __init__(self,
                 name,
                 deg_per_cycs=[10], #degrees
                 orientations=[45], #degrees
                 drift_frequencies=[0], #hz
                 phases=np.linspace(start=-np.pi,stop=np.pi,num=8,endpoint=True),
                 contrasts=[1],
                 durations=[1], #seconds
                 radii=[400], #degrees
                 iti=1., #seconds
                 itl=0., #inter trial luminance
                 reinforcement_manager=reinfmgr.NoReinforcement(),
                 **kwargs):
        super(Gratings,self).__init__(iti=iti, itl=itl)
        self.ver = Ver('0.0.1')
        self.reinforcement_manager = reinforcement_manager
        self.name = name
        self.deg_per_cycs = deg_per_cycs
        self.orientations = orientations
        self.drift_frequencies = drift_frequencies
        self.phases = phases
        self.contrasts = contrasts
        self.durations = durations
        self.radii = radii

    def __repr__(self):
        return "Gratings object with or:%s, tf:%s, ctr:%s and durs:%s)" % (self.orientations, self.drift_frequencies, self.contrasts, self.durations)

    def calc_stim(self, trial_record, station, **kwargs):

        (H, W, Hz) = self.choose_resolution(station=station, **kwargs)
        resolution = (H,W,Hz)
        target_ports = None
        distractor_ports = station.get_ports()

        # select from values
        stimulus = dict()
        stimulus['deg_per_cyc'] = random.choice(self.deg_per_cycs)
        stimulus['orientation'] = random.choice(self.orientations)
        stimulus['drift_frequency'] = random.choice(self.drift_frequencies)
        stimulus['phase'] = random.choice(self.phases)
        stimulus['contrast'] = random.choice(self.contrasts)
        stimulus['duration'] = random.choice(self.durations)
        stimulus['radius'] = random.choice(self.radii)
        stimulus['H'] = H
        stimulus['W'] = W
        stimulus['Hz'] = Hz

        trial_record['chosen_stim'] = stimulus

        frames_total = round(Hz*stimulus['duration'])

        port_details = {}
        port_details['target_ports'] = None
        port_details['distractor_ports'] = station.get_ports()

        return stimulus, resolution, frames_total, port_details

    def choose_resolution(self, station, **kwargs):
        H = 1080
        W = 1920
        Hz = 60
        return (H,W,Hz)

    def _setup_phases(self, trial_record, station, subject, **kwargs):
        """
        Gratings:_setupPhases is a simple trialManager. It is for autopilot
        It selects from PixPerCycs, Orientations, DriftFrequencies, Phases
        Contrasts, Durations and shows them one at a time. There is only one
        phase. Rewards may be provided and licks are recorded. There is no
        concept of punishment
        """
        (stimulus_details,resolution,frames_total,port_details) = self.calc_stim(trial_record=trial_record, station=station)
        hz = resolution[2]
        reward_size, request_reward_size, ms_penalty, ms_reward_sound, ms_penalty_sound = self.reinforcement_manager.calculate_reinforcement(subject=subject)
        reward_size = np.round(reward_size/1000*hz)

        # sounds
        trial_start_sound = station._sounds['trial_start_sound']
        trial_start_sound.secs = 0.1
        trial_start_sound.seek(0.)
        trial_start_sound.status= NOT_STARTED
        reward_sound = station._sounds['reward_sound']
        reward_sound.secs = 0.1
        reward_sound.seek(0.)
        reward_sound.status = NOT_STARTED

        self._Phases = []
        # Just display stim
        do_nothing = ()

        # the stimulus
        self._Phases.append(ps.StimPhaseSpec(
            phase_number=0,
            stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',mask=None,autoLog=False),
            stimulus_update_fn=Gratings.update_stimulus,
            stimulus_details=stimulus_details,
            transitions={do_nothing: 1},
            frames_until_transition=frames_total,
            auto_trigger=False,
            phase_type='stimulus',
            phase_name='stim',
            hz=hz,
            sounds_played=[trial_start_sound],
            is_last_phase=False))

        # reward if its provided
        if reward_size>0:
            # pre-reward
            self._Phases.append(ps.PhaseSpec(
                phase_number=1,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_details=None,
                stimulus_update_fn=btm.BaseTrialManager.do_nothing_to_stim,
                transitions={do_nothing: 2},
                frames_until_transition=6, # 6 frames to make the sound finish before reward
                auto_trigger=False,
                phase_type='pre-reward',
                phase_name='pre-reward_phase_spec',
                hz=hz,
                sounds_played=None,
                reward_valve='reward_valve'))
            # reward
            self._Phases.append(ps.RewardPhaseSpec(
                phase_number=2,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_details=None,
                stimulus_update_fn=btm.BaseTrialManager.do_nothing_to_stim,
                transitions={do_nothing: 3},
                frames_until_transition=reward_size,
                auto_trigger=False,
                phase_type='reward',
                phase_name='reward_phase',
                hz=hz,
                sounds_played=[reward_sound],
                reward_valve='reward_valve'))
            # itl
            self._Phases.append(ps.PhaseSpec(
                phase_number=3,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=(self.itl),autoLog=False),
                stimulus_details=None,
                stimulus_update_fn=btm.BaseTrialManager.do_nothing_to_stim,
                transitions=None,
                frames_until_transition=round(self.iti*hz),
                auto_trigger=False,
                phase_type='inter-trial',
                phase_name='inter-trial',
                hz=hz,
                sounds_played=None,
                is_last_phase=True))
        else:
            # itl
            self._Phases.append(ps.PhaseSpec(
                phase_number=1,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=(self.itl),autoLog=False),
                stimulus_details=None,
                stimulus_update_fn=btm.BaseTrialManager.do_nothing_to_stim,
                transitions=None,
                frames_until_transition=round(self.iti*hz),
                auto_trigger=False,
                phase_type='inter-trial',
                phase_name='inter-trial',
                hz=hz,
                sounds_played=None,
                is_last_phase=True))

        self._compiler = Gratings.trial_compiler

    def _simulate(self):
        station = st.StandardKeyboardStation()
        station.initialize()

        trial_record = {}
        quit = False
        while not quit:
            trial_record,quit = self.do_trial(trial_record=trial_record,station=station,subject=None,compiled_record=None,quit=quit)
        station.close_window()

    def decache(self):
        self._Phases = dict()

    @staticmethod
    def update_stimulus(stimulus,details):
        if details['drift_frequency'] !=0:
            stimulus.phase += float(details['drift_frequency'])/float(details['Hz'])

    def do_trial(self, station, subject, trial_record, compiled_record,quit):
        # returns quit and trial_record
        # resetup the window according to the itl

        # check if okay to run the trial manager with the station
        if not self.station_ok_for_tm(station):
            print('GRATINGS:DO_TRIAL:Station not ok for TM')
            quit = True
            trial_record['correct'] = None
            trial_record['errored_out'] = True
            return trial_record,quit

        ## _setup_phases
        self._setup_phases(trial_record=trial_record, station=station,compiled_record=compiled_record,subject=subject)
        station._key_pressed = []

        trial_record,quit = super(Gratings,self).do_trial(station=station, subject=subject, trial_record=trial_record, compiled_record=compiled_record, quit=quit)
        return trial_record,quit

    @staticmethod
    def trial_compiler(compiled_record, trial_record):
        print('GRATINGS:TRIAL_COMPILER::compiling trial')

        try:
            import pprint
            ppr = pprint.PrettyPrinter(indent=4).pprint
            ppr(compiled_record)
            compiled_details = compiled_record['compiled_details']['Gratings']
        except KeyError as e:
            traceback.print_stack()
            compiled_details = {}
            compiled_details['trial_number'] = []
            compiled_details['deg_per_cyc'] = []
            compiled_details['orientation'] = []
            compiled_details['drift_frequency'] = []
            compiled_details['phase'] = []
            compiled_details['contrast'] = []
            compiled_details['duration'] = []
            compiled_details['radius'] = []
            # compiled_details['radius_type'] = []
            compiled_details['location'] = []
            compiled_details['H'] = []
            compiled_details['W'] = []
            compiled_details['Hz'] = []
            # put an empty compiled_details in the compiled_records
            compiled_record['compiled_details']['Gratings'] = compiled_details

        compiled_details['trial_number'].append(trial_record['trial_number'])
        compiled_details['deg_per_cyc'].append(trial_record['chosen_stim']['deg_per_cyc'])
        compiled_details['orientation'].append(trial_record['chosen_stim']['orientation'])
        compiled_details['drift_frequency'].append(trial_record['chosen_stim']['drift_frequency'])
        compiled_details['phase'].append(trial_record['chosen_stim']['phase'])
        compiled_details['contrast'].append(trial_record['chosen_stim']['contrast'])
        compiled_details['duration'].append(trial_record['chosen_stim']['duration'])
        compiled_details['radius'].append(trial_record['chosen_stim']['radius'])
        compiled_details['radius_type'].append('None')
        compiled_details['location'].append(trial_record['chosen_stim']['location'])
        compiled_details['H'].append(trial_record['chosen_stim']['H'])
        compiled_details['W'].append(trial_record['chosen_stim']['W'])
        compiled_details['Hz'].append(trial_record['chosen_stim']['Hz'])

        compiled_record['compiled_details'] = compiled_details

        return compiled_details

    @staticmethod
    def station_ok_for_tm(station):
        if station.__class__.__name__ in ['StandardVisionBehaviorStation','StandardVisionHeadfixStation','StandardKeyboardStation']:
            return True
        else:
            return False


class Gratings_GaussianEdge(Gratings):
    """
        GRATINGS_GAUUIANEDGE defines a standard gratings trial manager
        with a gaussian edge for a view port

            RadiusType = "HardEdge"
            Scale = "ScaleToHeight"

        VERSION HISTORY:
        0.0.1 : first commit
        0.0.2 : lean into Gratings subclass. Cleaned out method calls
    """


    def __init__(self, name, **kwargs):
        self.ver = Ver('0.0.2')
        super(Gratings_GaussianEdge, self).__init__(name, **kwargs)

    def __repr__(self):
        return "Gratings_GaussianEdge object with or:%s, tf:%s, ctr:%s and durs:%s)" % (self.orientations, self.drift_frequencies, self.contrasts, self.durations)

    def _setup_phases(self, trial_record, station, subject, **kwargs):
        """
        Gratings:_setupPhases is a simple trialManager. It is for autopilot
        It selects from PixPerCycs, Orientations, DriftFrequencies, Phases
        Contrasts, Durations and shows them one at a time. There is only one
        phase. There is no "correct" and no responses are required/recorded

        TODO:
        1. add rewards to this
        """
        super(Gratings_GaussianEdge,self)._setup_phases(trial_record, station, **kwargs)

        # replace for the first phase
        self._Phases[0].stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',mask='gauss',autoLog=False)
        self._compiler = Gratings_GaussianEdge.trial_compiler

    @staticmethod
    def trial_compiler(compiled_record, trial_record):
        try:
            compiled_details = compiled_record['compiled_details']['Gratings']
        except KeyError:
            compiled_details = {}
            compiled_details['trial_number'] = []
            compiled_details['deg_per_cyc'] = []
            compiled_details['orientation'] = []
            compiled_details['drift_frequency'] = []
            compiled_details['phase'] = []
            compiled_details['contrast'] = []
            compiled_details['duration'] = []
            compiled_details['radius'] = []
            compiled_details['radius_type'] = []
            compiled_details['location'] = []
            compiled_details['H'] = []
            compiled_details['W'] = []
            compiled_details['Hz'] = []
            # put an empty compiled_details in the compiled_records
            compiled_record['compiled_details']['Gratings'] = compiled_details

        compiled_details['trial_number'].append(trial_record['trial_number'])
        compiled_details['deg_per_cyc'].append(trial_record['chosen_stim']['deg_per_cyc'])
        compiled_details['orientation'].append(trial_record['chosen_stim']['orientation'])
        compiled_details['drift_frequency'].append(trial_record['chosen_stim']['drift_frequency'])
        compiled_details['phase'].append(trial_record['chosen_stim']['phase'])
        compiled_details['contrast'].append(trial_record['chosen_stim']['contrast'])
        compiled_details['duration'].append(trial_record['chosen_stim']['duration'])
        compiled_details['radius'].append(trial_record['chosen_stim']['radius'])
        compiled_details['radius_type'].append('Gaussian')
        compiled_details['location'].append(trial_record['chosen_stim']['location'])
        compiled_details['H'].append(trial_record['chosen_stim']['H'])
        compiled_details['W'].append(trial_record['chosen_stim']['W'])
        compiled_details['Hz'].append(trial_record['chosen_stim']['Hz'])

        compiled_record['compiled_details'] = compiled_details

        return compiled_details


class Gratings_HardEdge(Gratings):
    """
        GRATINGS_HARDEDGE defines a standard gratings trial manager
        with hard edges for a view port

        VERSION HISTORY:
        0.0.1 : first commit
        0.0.2 : lean into Gratings subclass. Cleaned out method calls
    """

    def __init__(self, name, **kwargs):
        self.ver = Ver('0.0.2')
        super(Gratings_HardEdge, self).__init__(name, **kwargs)

    def __repr__(self):
        return "Gratings_HardEdge object with or:%s, tf:%s, ctr:%s and durs:%s)" % (self.orientations, self.drift_frequencies, self.contrasts, self.durations)

    def _setup_phases(self, trial_record, station, subject, **kwargs):
        """
        Gratings:_setupPhases is a simple trialManager. It is for autopilot
        It selects from PixPerCycs, Orientations, DriftFrequencies, Phases
        Contrasts, Durations and shows them one at a time. There is only one


        TODO:
        1. add rewards to this
        """
        super(Gratings_GaussianEdge,self)._setup_phases(trial_record, station, **kwargs)

        self._Phases[0].stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',mask='circle',autoLog=False)
        self._compiler = Gratings_HardEdge.trial_compiler

    @staticmethod
    def trial_compiler(compiled_record, trial_record):
        try:
            compiled_details = compiled_record['compiled_details']['Gratings']
        except KeyError:
            compiled_details = {}
            compiled_details['trial_number'] = []
            compiled_details['deg_per_cyc'] = []
            compiled_details['orientation'] = []
            compiled_details['drift_frequency'] = []
            compiled_details['phase'] = []
            compiled_details['contrast'] = []
            compiled_details['duration'] = []
            compiled_details['radius'] = []
            compiled_details['radius_type'] = []
            compiled_details['location'] = []
            compiled_details['H'] = []
            compiled_details['W'] = []
            compiled_details['Hz'] = []
            # put an empty compiled_details in the compiled_records
            compiled_record['compiled_details']['Gratings'] = compiled_details

        compiled_details['trial_number'].append(trial_record['trial_number'])
        compiled_details['deg_per_cyc'].append(trial_record['chosen_stim']['deg_per_cyc'])
        compiled_details['orientation'].append(trial_record['chosen_stim']['orientation'])
        compiled_details['drift_frequency'].append(trial_record['chosen_stim']['drift_frequency'])
        compiled_details['phase'].append(trial_record['chosen_stim']['phase'])
        compiled_details['contrast'].append(trial_record['chosen_stim']['contrast'])
        compiled_details['duration'].append(trial_record['chosen_stim']['duration'])
        compiled_details['radius'].append(trial_record['chosen_stim']['radius'])
        compiled_details['radius_type'].append('Circular')
        compiled_details['location'].append(trial_record['chosen_stim']['location'])
        compiled_details['H'].append(trial_record['chosen_stim']['H'])
        compiled_details['W'].append(trial_record['chosen_stim']['W'])
        compiled_details['Hz'].append(trial_record['chosen_stim']['Hz'])

        compiled_record['compiled_details'] = compiled_details

        return compiled_details
##########################################################################################
##########################################################################################
####################### AFC GRATINGS TRIAL MANAGERS - SHOWS ##############################
############################# ONE GRATING AT A TIME ######################################
##########################################################################################
##########################################################################################

class Gratings2AFC(btm.BaseTrialManager):
    """
        GRATINGS2AFC defines a standard gratings trial manager
            deg_per_cycs
            orientations
            drift_frequencies
            phases
            contrasts
            durations
            radii # in units of "Scale"
            positions

            VERSION HISTORY:
            0.0.1 : Initial design
            0.0.2 : (1) itl and iti sent to BTM and (2) _setup_phases() are zero-indexed
                    (3) renamed ports to appropriate names (4) forced to 2-AFC
    """
    _current_is_catch = False

    def __init__(self,
                 name = 'DemoGratings2AFCTrialManager',
                 deg_per_cycs = {'left_port':[10],'right_port':[10]},
                 orientations = {'left_port':[-np.pi / 4], 'right_port':[np.pi / 4]},
                 drift_frequencies = {'left_port':[0],'right_port':[0]},
                 phases = {'left_port':np.linspace(start=-np.pi,stop=np.pi,num=8,endpoint=True),'right_port':np.linspace(start=-np.pi,stop=np.pi,num=8, endpoint=True)},
                 contrasts = {'left_port':[1],'right_port':[1]},
                 durations = {'left_port':[float('Inf')],'right_port':[float('Inf')]},
                 locations = {'left_port':[(0.5,0.5)],'right_port':[(0.5,0.5)]},
                 radii = {'left_port':[40],'right_port':[40]},
                 radius_type = 'Circular',
                 left_port_probability = 0.5,
                 catch_trial_probability = 0.2,
                 iti = 1,
                 itl = 0.,
                 do_combos = True,
                 reinforcement_manager = reinfmgr.NoReinforcement(),
                 **kwargs):
        super(Gratings2AFC,self).__init__(iti=iti,itl=itl)
        self.ver = Ver('0.0.2')
        self.name = name
        self.reinforcement_manager = reinforcement_manager

        self.do_combos = do_combos
        self.deg_per_cycs = deg_per_cycs
        self.orientations = orientations
        self.drift_frequencies = drift_frequencies
        self.phases = phases
        self.contrasts = contrasts
        self.durations = durations
        self.locations = locations
        self.radii = radii
        self.radius_type = radius_type

        self.left_port_probability = left_port_probability
        self.catch_trial_probability = catch_trial_probability

        self._verify_params_ok()

    def _verify_params_ok(self):
        n_afc = 2
        assert len(self.deg_per_cycs)==n_afc,'GRATINGS2AFC::INIT::orientations not same length as %r' % n_afc
        assert len(self.orientations)==n_afc,'GRATINGS2AFC::INIT::orientations not same length as %r' % n_afc
        assert len(self.drift_frequencies)==n_afc,'GRATINGS2AFC::INIT::drift_frequencies not same length as %r' % n_afc
        assert len(self.phases)==n_afc,'GRATINGS2AFC::INIT::phases not same length as %r' % n_afc
        assert len(self.contrasts)==n_afc,'GRATINGS2AFC::INIT::contrasts not same length as %r' % n_afc
        assert len(self.durations)==n_afc,'GRATINGS2AFC::INIT::durations not same length as %r' % n_afc
        assert len(self.locations)==n_afc,'GRATINGS2AFC::INIT::locations not same length as %r' % n_afc
        assert len(self.radii)==n_afc,'GRATINGS2AFC::INIT::radii not same length as %r' % n_afc

        if do_combos:
            # if do_combos, don't have to worry about the lengths of each values
            pass
        else:
            num_options_L = len(self.deg_per_cycs['left_port'])
            assert len(self.orientations['left_port'])==num_options_L,'GRATINGS2AFC::INIT::L orientations not same length as deg_per_cycs'
            assert len(self.drift_frequencies['left_port'])==num_options_L,'GRATINGS2AFC::INIT::L drift_frequencies not same length as deg_per_cycs'
            assert len(self.phases['left_port'])==num_options_L,'GRATINGS2AFC::INIT::L phases not same length as deg_per_cycs'
            assert len(self.contrasts['left_port'])==num_options_L,'GRATINGS2AFC::INIT::L contrasts not same length as deg_per_cycs'
            assert len(self.durations['left_port'])==num_options_L,'GRATINGS2AFC::INIT::L durations not same length as deg_per_cycs'
            assert len(self.locations['left_port'])==num_options_L,'GRATINGS2AFC::INIT::L locations not same length as deg_per_cycs'
            assert len(self.radii['left_port'])==num_options_L,'GRATINGS2AFC::INIT::L radii not same length as deg_per_cycs'

            num_options_R = len(self.deg_per_cycs['right_port'])
            assert len(self.orientations['right_port'])==num_options_R,'GRATINGS2AFC::INIT::R orientations not same length as deg_per_cycs'
            assert len(self.drift_frequencies['right_port'])==num_options_R,'GRATINGS2AFC::INIT::R drift_frequencies not same length as deg_per_cycs'
            assert len(self.phases['right_port'])==num_options_R,'GRATINGS2AFC::INIT::R phases not same length as deg_per_cycs'
            assert len(self.contrasts['right_port'])==num_options_R,'GRATINGS2AFC::INIT::R contrasts not same length as deg_per_cycs'
            assert len(self.durations['right_port'])==num_options_R,'GRATINGS2AFC::INIT::R durations not same length as deg_per_cycs'
            assert len(self.locations['right_port'])==num_options_R,'GRATINGS2AFC::INIT::R locations not same length as deg_per_cycs'
            assert len(self.radii['right_port'])==num_options_R,'GRATINGS2AFC::INIT::R radii not same length as deg_per_cycs'

        assert self.radius_type in ['Circular','Gaussian'], 'GRATINGS2AFC::INIT::Unrecognized radius_type:%s' % self.radius_type

    def __repr__(self):
        return "GRATINGS2AFC object"

    @staticmethod
    def update_stimulus(stimulus,details):
        if details['drift_frequency'] !=0:
            stimulus.phase += float(details['drift_frequency'])/float(details['Hz'])

    def choose_ports(self, trial_record, compiled_record, station,):
        if not compiled_record['trial_manager_class'][-1] == 'BCore.Classes.TrialManagers.GratingsTrialManagers.Gratings2AFC':
            pass
        return 'left_port'

    def do_trial(self, station, subject, trial_record, compiled_record,quit):
        # returns quit and trial_record
        # resetup the window according to the itl

        # check if okay to run the trial manager with the station
        if not self.station_ok_for_tm(station):
            quit = True
            trial_record['correct'] = None
            trial_record['errored_out'] = True
            return trial_record,quit


        ## _setup_phases
        self._setup_phases(trial_record=trial_record, station=station,compiled_record=compiled_record, subject=subject)
        station._key_pressed = []

        current_phase_num = 0

        # was on will be used to check for new responses
        was_on = {'L':False, 'C': False, 'R':False}

        # Zero out the trial clock
        trial_clock = station._clocks['trial_clock']
        trial_clock.reset()

        trial_done = False
        error_out = False

        trial_record['errored_out'] = False
        trial_record['manual_quit'] = False


        trial_record['reinforcement_manager_name'] = self.reinforcement_manager.name
        trial_record['reinforcement_manager_class'] = self.reinforcement_manager.__class__.__name__
        trial_record['reinforcement_manager_version_number'] = self.reinforcement_manager.ver.__str__()

        trial_record['phase_data'] = []

        station.set_trial_pin_on()
        ### loop into trial phases
        while not trial_done and not error_out and not quit:
            # current_phase_num determines the phase
            phase = self._Phases[current_phase_num]

            # collect details about the phase
            frames_until_transition = phase.frames_until_transition
            stim = phase.stimulus
            stim_details = phase.stimulus_details
            transition = phase.transitions
            if not transition:
                is_last_phase = True
            else:
                is_last_phase = False
            auto_trigger = phase.auto_trigger
            if phase.sounds_played:
                sound = phase.sounds_played[0]
                sound_duration = phase.sounds_played[1]
                sound.seek(0.)
                sound_started = False
                sound_done = False
                sound_timer = psychopy.core.CountdownTimer(sound_duration)
            else:
                sound = None

            # save relevant data into phase_data
            phase_data = {}
            phase_data['phase_name'] = phase.phase_name
            phase_data['phase_number'] = phase.phase_number
            phase_data['enter_time'] = trial_clock.getTime()
            phase_data['response'] = []
            phase_data['response_time'] = []

            # loop into phase
            phase_done = False
            trial_record = phase.on_enter(trial_record=trial_record, station=station)
            while not phase_done and not error_out and not quit:
                # deal with sounds
                if sound:
                    if not sound_started:
                        sound.play()
                        sound_timer.reset()
                        sound_started = True

                    if sound_timer.getTime() <0 and not sound_done:
                        sound.stop()
                        sound_done = True

                # deal with stim
                if stim:
                    stim.draw()
                    if phase.phase_name=='stim':
                        psychopy.visual.Rect(station._window,pos=(-300,-300),width=100,height=100,units='pix',fillColor=(1,1,1)).draw()
                    phase.stimulus_update_fn(stim,stim_details)
                phase.on_frame(station=station,trial_record=trial_record)

                # look for responses
                response_led_to_transition = False
                response = station.read_ports()
                if len(response)>1:
                    error_out = True
                    trial_record['errored_out'] = True
                elif len(response)==1:
                    response = response[0]
                    try:
                        current_phase_num = transition[response] - 1
                        response_led_to_transition = True
                    except KeyError:
                        response_led_to_transition = False # that phase did not have a transition for that response
                    except TypeError:
                        assert is_last_phase, 'No reason why it should come here otherwise'
                    finally:
                        # logit but only if was_on wasnt already on
                        if not was_on[response]:
                            phase_data['response'].append(response)
                            phase_data['response_time'].append(trial_clock.getTime())
                    was_on[response] = True # flip was on to true after we used it to check for new events
                else:
                    pass

                # update the frames_until_transition and check if the phase is done
                # phase is done when there are no more frames in the phase or is we flipped due to transition
                # however we can stop playing the phase because we manual_quit or because we errored out
                frames_until_transition = frames_until_transition-1
                frames_led_to_transition = False
                if frames_until_transition==0:
                    frames_led_to_transition = True
                    if transition: current_phase_num = transition[None] - 1
                    else: current_phase_num = None # the last phase has no

                if frames_led_to_transition or response_led_to_transition:
                    phase_done = True
                manual_quit = station.check_manual_quit()
                if manual_quit:
                    trial_record['manual_quit'] = True
                    trial_record['correct'] = None
                quit = quit or manual_quit
            trial_record = phase.on_exit(trial_record=trial_record, station=station)
            trial_record['phase_data'].append(phase_data)

            # when do we quit the trial? trial_done only when last phjase
            # but we can exit if manual_quit or errored out
            if is_last_phase: trial_done = True
        station.set_trial_pin_off()
        return trial_record,quit

    def calc_stim(self, trial_record, station, **kwargs):
        (H, W, Hz) = self.choose_resolution(station=station, **kwargs)
        resolution = (H,W,Hz)
        all_ports = ('left_port','center_port','right_port')
        request_port = 'center_port'
        response_ports = tuple(np.setdiff1d(all_ports,request_port))
        target_port = np.random.choice(response_ports)
        distractor_port = tuple(np.setdiff1d(response_ports,target_port))

        distractor_port = distractor_port[0]
        # select from values
        stimulus = dict()
        stimulus['deg_per_cyc'] = random.choice(self.deg_per_cycs[target_port])
        stimulus['orientation'] = random.choice(self.orientations[target_port])
        stimulus['drift_frequency'] = random.choice(self.drift_frequencies[target_port])
        stimulus['phase'] = random.choice(self.phases[target_port])
        stimulus['contrast'] = random.choice(self.contrasts[target_port])
        stimulus['duration'] = random.choice(self.durations[target_port])
        stimulus['location'] = random.choice(self.locations[target_port])
        stimulus['radius'] = random.choice(self.radii[target_port])
        stimulus['radius_type'] = self.radius_type
        stimulus['H'] = H
        stimulus['W'] = W
        stimulus['Hz'] = Hz

        trial_record['chosen_stim'] = stimulus

        frames_total = round(Hz*stimulus['duration'])

        port_details = {}
        port_details['request_port'] = request_port
        port_details['target_port'] = target_port
        port_details['distractor_port'] = distractor_port

        return stimulus, resolution, frames_total, port_details

    def choose_resolution(self, station, **kwargs):
        H = 1080
        W = 1920
        Hz = 60
        return (H,W,Hz)

    def _setup_phases(self, trial_record, station, subject, **kwargs):
        """
        GratingsAFC:_setup_phases
        1. Pre-trial: gray screen. REQUEST_PORT -> 2
        2. Stimulus: Grating stimulus. RESPONSE_PORT==TARGET_PORT -> CORRECT, else PUNISH
        3. Correct: Give reward
        4. Punish: Timeout
        5. ITI: Gray screen of duration iti,
        """
        (stimulus_details,resolution,frames_total,port_details) = self.calc_stim(trial_record=trial_record, station=station)
        hz = resolution[2]
        do_nothing = ()
        if port_details['target_port'] == 'left_port':
            reward_valve = 'left_valve'
        elif port_details['target_port'] == 'right_port':
            reward_valve = 'right_valve'
        elif port_details['target_port'] == 'center_port':
            reward_valve = 'center_valve'

        if stimulus_details['duration']==float('inf'):
            do_post_discrim_stim = False
        else:
            do_post_discrim_stim = True

        self._Phases = []

        reward_size, request_reward_size, ms_penalty, ms_reward_sound, ms_penalty_sound = self.reinforcement_manager.calculate_reinforcement(subject=subject)
        reward_size = np.round(reward_size/1000*60)
        request_reward_size = np.round(request_reward_size/1000*60)
        penalty_size = np.round(ms_penalty/1000*60)
        if do_post_discrim_stim:
            self._Phases.append(ps.PhaseSpec(
                phase_number=0,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                stimulus_details=None,
                transitions={port_details['request_port']: 2},
                frames_until_transition=float('inf'),
                auto_trigger=False,
                phase_type='pre-request',
                phase_name='pre-request',
                hz=hz,
                sounds_played=(station._sounds['trial_start_sound'], 0.050)))
            if self.radius_type=='Gaussian':
                self._Phases.append(ps.PhaseSpec(
                    phase_number=1,
                    stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],mask='gauss',ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',autoLog=False),
                    stimulus_update_fn=GratingsAFC.update_stimulus,
                    stimulus_details=stimulus_details,
                    transitions={do_nothing: 3, port_details['target_port']: 4, port_details['distractor_port']: 5},
                    frames_until_transition=frames_total,
                    auto_trigger=False,
                    phase_type='stimulus',
                    phase_name='stim',
                    hz=hz,
                    sounds_played=(station._sounds['stim_start_sound'], 0.050)))
            else:
                self._Phases.append(ps.PhaseSpec(
                    phase_number=1,
                    stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],mask='circle',ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',autoLog=False),
                    stimulus_update_fn=GratingsAFC.update_stimulus,
                    stimulus_details=stimulus_details,
                    transitions={do_nothing: 3, port_details['target_port']: 4, port_details['distractor_port']: 5},
                    frames_until_transition=frames_total,
                    auto_trigger=False,
                    phase_type='stimulus',
                    phase_name='stim',
                    hz=hz,
                    sounds_played=(station._sounds['stim_start_sound'], 0.050)))
            self._Phases.append(ps.PhaseSpec(
                phase_number=2,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                stimulus_details=None,
                transitions={port_details['target_port']: 4, port_details['distractor_port']: 5},
                frames_until_transition=float('inf'),
                auto_trigger=False,
                phase_type='post-stimulus',
                phase_name='post-stim',
                hz=hz,
                sounds_played=None))
            self._Phases.append(ps.RewardPhaseSpec(
                phase_number=3,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                stimulus_details=None,
                transitions={do_nothing: 6},
                frames_until_transition=reward_size,
                auto_trigger=False,
                phase_type='reinforcement',
                phase_name='reward',
                hz=hz,
                sounds_played=(station._sounds['correct_sound'], ms_reward_sound/1000),
                reward_valve=reward_valve))
            self._Phases.append(ps.PunishmentPhaseSpec(
                phase_number=4,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=(0.,0.,0.,),autoLog=False),
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                stimulus_details=None,
                transitions={do_nothing: 6},
                frames_until_transition=penalty_size,
                auto_trigger=False,
                phase_type='reinforcement',
                phase_name='punishment',
                hz=hz,
                sounds_played=(station._sounds['punishment_sound'],ms_penalty_sound/1000)))
            self._Phases.append(ps.PhaseSpec(
                phase_number=5,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_details=None,
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                transitions=None,
                frames_until_transition=round(self.iti*hz),
                auto_trigger=False,
                phase_type='inter-trial',
                phase_name='inter-trial',
                hz=hz,
                sounds_played=(station._sounds['trial_end_sound'], 0.050)))
        else:
            self._Phases.append(ps.PhaseSpec(
                phase_number=0,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                stimulus_details=None,
                transitions={port_details['request_port']: 2},
                frames_until_transition=float('inf'),
                auto_trigger=False,
                phase_type='pre-request',
                phase_name='pre-request',
                hz=hz,
                sounds_played=(station._sounds['trial_start_sound'], 0.050)))
            if self.radius_type=='Gaussian':
                self._Phases.append(ps.PhaseSpec(
                    phase_number=1,
                    stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],mask='gauss',ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',autoLog=False),
                    stimulus_update_fn=GratingsAFC.update_stimulus,
                    stimulus_details=stimulus_details,
                    transitions={port_details['target_port']: 3, port_details['distractor_port']: 4},
                    frames_until_transition=float('inf'),
                    auto_trigger=False,
                    phase_type='stimulus',
                    phase_name='stim',
                    hz=hz,
                    sounds_played=(station._sounds['stim_start_sound'], 0.050)))
            else:
                self._Phases.append(ps.PhaseSpec(
                    phase_number=1,
                    stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],mask='circle',ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',autoLog=False),
                    stimulus_update_fn=GratingsAFC.update_stimulus,
                    stimulus_details=stimulus_details,
                    transitions={port_details['target_port']: 3, port_details['distractor_port']: 4},
                    frames_until_transition=float('inf'),
                    auto_trigger=False,
                    phase_type='stimulus',
                    phase_name='stim',
                    hz=hz,
                    sounds_played=(station._sounds['stim_start_sound'], 0.050)))
            self._Phases.append(ps.RewardPhaseSpec(
                phase_number=2,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                stimulus_details=None,
                transitions={do_nothing: 5},
                frames_until_transition=reward_size,
                auto_trigger=False,
                phase_type='reinforcement',
                phase_name='reward',
                hz=hz,
                sounds_played=(station._sounds['correct_sound'], ms_reward_sound/1000),
                reward_valve=reward_valve))
            self._Phases.append(ps.PunishmentPhaseSpec(
                phase_number=3,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=(0,0,0,),autoLog=False),
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                stimulus_details=None,
                transitions={do_nothing: 5},
                frames_until_transition=penalty_size,
                auto_trigger=False,
                phase_type='reinforcement',
                phase_name='punishment',
                hz=hz,
                sounds_played=(station._sounds['punishment_sound'],ms_penalty_sound/1000)))
            self._Phases.append(ps.PhaseSpec(
                phase_number=4,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_details=None,
                stimulus_update_fn=GratingsAFC.do_nothing_to_stim,
                transitions=None,
                frames_until_transition=round(self.iti*hz),
                auto_trigger=False,
                phase_type='inter-trial',
                phase_name='inter-trial',
                hz=hz,
                sounds_played=(station._sounds['trial_end_sound'], 0.050)))

    @staticmethod
    def station_ok_for_tm(station):
        if station.__class__.__name__ in ['StandardVisionBehaviorStation','StandardKeyboardStation']:
            return True
        else:
            return False

    def trial_compiler(self, compiled_record, trial_record):
        try:
            compiled_details = compiled_record['compiled_details']['GratingsAFC']
        except KeyError:
            compiled_details = {}
            compiled_details['trial_number'] = []
            compiled_details['deg_per_cyc'] = []
            compiled_details['orientation'] = []
            compiled_details['drift_frequency'] = []
            compiled_details['phase'] = []
            compiled_details['contrast'] = []
            compiled_details['duration'] = []
            compiled_details['location'] = []
            compiled_details['radius'] = []
            compiled_details['radius_type'] = []
            compiled_details['H'] = []
            compiled_details['W'] = []
            compiled_details['Hz'] = []
            # specific to animal responses
            compiled_details['request_time'] = [] # time from trial start to center request
            compiled_details['response_time'] = [] # time from request to response
            compiled_details['request_lick_timings'] = []
            compiled_details['response_lick_timings_prev_trial'] = []
            # put an empty compiled_details in the compiled_records
            compiled_record['compiled_details']['Gratings'] = compiled_details

        compiled_details['trial_number'].append(trial_record['trial_number'])
        compiled_details['deg_per_cyc'].append(trial_record['chosen_stim']['deg_per_cyc'])
        compiled_details['orientation'].append(trial_record['chosen_stim']['orientation'])
        compiled_details['drift_frequency'].append(trial_record['chosen_stim']['drift_frequency'])
        compiled_details['phase'].append(trial_record['chosen_stim']['phase'])
        compiled_details['contrast'].append(trial_record['chosen_stim']['contrast'])
        compiled_details['duration'].append(trial_record['chosen_stim']['duration'])
        compiled_details['location'].append(trial_record['chosen_stim']['location'])
        compiled_details['radius'].append(trial_record['chosen_stim']['radius'])
        compiled_details['radius_type'].append(self.radius_type)
        compiled_details['H'].append(trial_record['chosen_stim']['H'])
        compiled_details['W'].append(trial_record['chosen_stim']['W'])
        compiled_details['Hz'].append(trial_record['chosen_stim']['Hz'])

        # animal response data compilation
        phase_data = trial_record['phase_data']
        phase_types = np.asarray([p['phase_type'] for p in phase_data])
        pre_req_phase_num = np.argwhere(phase_types=='pre-request')
        stim_phase_num = np.argwhere(phase_types=='stimulus')
        reinf_phase_num = np.argwhere(phase_types=='reinforcement')
        # request_time is time from TRIAL_START to 'stim' phase enter_time
        compiled_details['request_time'].append(phase_data[stim_phase_num]['enter_time'])
        # resonse_time is time from 'stim' phase enter_time to 'reinforcement' phase enter time
        compiled_details['response_time'].append(phase_data[reinf_phase_num]['enter_time']-phase_data[stim_phase_num]['enter_time'])
        # request_lick_timings are center_port' licks in the stim_phase
        lick_loc = np.asarray(phase_data[stim_phase_num]['response'])
        lick_times = np.asarray(phase_data[stim_phase_num]['response_time'])
        which_licks = np.argwhere(lick_loc=='center_port')
        compiled_details['request_lick_timings'].append(lick_times[which_licks])
        # response_lick_timings_prev_trial are non 'center_port' licks in the pre_req_phase_num
        lick_loc = np.asarray(phase_data[pre_req_phase_num]['response'])
        lick_times = np.asarray(phase_data[pre_req_phase_num]['response_time'])
        which_licks = np.argwhere(lick_loc!='center_port')
        compiled_details['response_lick_timings_prev_trial'].append(lick_times[which_licks])




        compiled_record['compiled_details'] = compiled_details

        return compiled_details


##########################################################################################
##########################################################################################
####################### GNG GRATINGS TRIAL MANAGERS - SHOWS ##############################
############################# ONE GRATING AT A TIME ######################################
##########################################################################################
##########################################################################################

class GratingsGoNoGo(btm.BaseTrialManager):
    """
        GRATINGSGONOGO defines a standard gratings trial manager for Go-No-Go trials. Requires:
            deg_per_cycs
            orientations
            drift_frequencies
            phases
            contrasts
            durations
            radii # in units of "Scale"
            locations

            do_combos
            reinforcement_manager

            VERSION HISTORY:
            0.0.1 : Initial design
            0.0.2 : (1) itl and iti sent to BTM and (2) _setup_phases()
                    are zero-indexed
    """

    def __init__(self,
                 name = 'DemoGratingsAFCTrialManager',
                 deg_per_cycs = {'G':[10],'N':[10]},
                 orientations = {'G':[-np.pi / 4], 'N':[np.pi / 4]},
                 drift_frequencies = {'G':[0],'N':[0]},
                 phases = {'G':np.linspace(start=-np.pi,stop=np.pi,num=8,endpoint=True),'N':np.linspace(start=-np.pi,stop=np.pi,num=8, endpoint=True)},
                 contrasts = {'G':[1],'N':[1]},
                 durations = {'G':[1.],'N':[1.]},
                 locations = {'G':[(0.5,0.5)],'N':[(0.5,0.5)]},
                 radii = {'G':[40],'N':[40]},
                 iti = 1.,
                 itl = 0.,
                 do_combos = True,
                 reinforcement_manager = reinfmgr.ConstantReinforcement(),
                 **kwargs):
        super(GratingsGoNoGo,self).__init__(iti=iti, itl=itl)
        self.ver = Ver('0.0.2')
        self.name = name
        self.reinforcement_manager = reinforcement_manager

        self.do_combos = do_combos
        self.deg_per_cycs = deg_per_cycs
        self.orientations = orientations
        self.drift_frequencies = drift_frequencies
        self.phases = phases
        self.contrasts = contrasts
        self.durations = durations
        self.locations = locations
        self.radii = radii

    def _verify_params_ok(self):
        assert isinstance(self.do_combos,bool)
        if self.do_combos:
            # if do_combos, don't have to worry about the lengths of each values
            pass
        else:
            num_options_G = len(self.deg_per_cycs['G'])
            assert len(self.orientations['G'])==num_options_G,'G orientations not same length as deg_per_cycs'
            assert len(self.drift_frequencies['G'])==num_options_G,'G drift_frequencies not same length as deg_per_cycs'
            assert len(self.phases['G'])==num_options_G,'G phases not same length as deg_per_cycs'
            assert len(self.contrasts['G'])==num_options_G,'G contrasts not same length as deg_per_cycs'
            assert len(self.durations['G'])==num_options_G,'G durations not same length as deg_per_cycs'
            assert len(self.locations['G'])==num_options_G,'G locations not same length as deg_per_cycs'
            assert len(self.radii['G'])==num_options_G,'G radii not same length as deg_per_cycs'

            num_options_N = len(self.deg_per_cycs['N'])
            assert len(self.orientations['N'])==num_options_N,'N orientations not same length as deg_per_cycs'
            assert len(self.drift_frequencies['N'])==num_options_N,'N drift_frequencies not same length as deg_per_cycs'
            assert len(self.phases['N'])==num_options_N,'N phases not same length as deg_per_cycs'
            assert len(self.contrasts['N'])==num_options_N,'N contrasts not same length as deg_per_cycs'
            assert len(self.durations['N'])==num_options_N,'N durations not same length as deg_per_cycs'
            assert len(self.locations['N'])==num_options_N,'N locations not same length as deg_per_cycs'
            assert len(self.radii['N'])==num_options_N,'N radii not same length as deg_per_cycs'

        assert np.logical_and(np.all(np.asarray(self.durations['G'])>0), np.all(np.asarray(self.durations['G'])<float('inf'))), 'All durations should be positive and finite'
        assert np.logical_and(np.all(np.asarray(self.durations['N'])>0), np.all(np.asarray(self.durations['N'])<float('inf'))), 'All durations should be positive and finite'

    def __repr__(self):
        return "GRATINGSGONOGO object"

    @staticmethod
    def update_stimulus(stimulus,details):
        if details['drift_frequency'] !=0:
            stimulus.phase += float(details['drift_frequency'])/float(details['Hz'])

    def do_trial(self, station, subject, trial_record, compiled_record,quit):
        # returns quit and trial_record
        # resetup the window according to the itl

        # check if okay to run the trial manager with the station
        if not self.station_ok_for_tm(station):
            print('GRATINGSGONOGO:DO_TRIAL: station not ok for tm')
            quit = True
            trial_record['correct'] = None
            trial_record['errored_out'] = True
            return trial_record,quit


        ## _setup_phases
        self._setup_phases(trial_record=trial_record, station=station,compiled_record=compiled_record, subject=subject)
        station._key_pressed = []

        trial_record,quit = super(GratingsGoNoGo,self).do_trial(station=station, subject=subject, trial_record=trial_record, compiled_record=compiled_record, quit=quit)
        return trial_record,quit

    def calc_stim(self, trial_record, station, **kwargs):
        (H, W, Hz) = self.choose_resolution(station=station, **kwargs)
        resolution = (H,W,Hz)
        all_ports = ('left_port','center_port','right_port')
        request_port = 'center_port'
        response_ports = tuple(np.setdiff1d(all_ports,request_port))
        target_port = np.random.choice(response_ports)
        distractor_port = tuple(np.setdiff1d(response_ports,target_port))

        distractor_port = distractor_port[0]
        # select from values
        stimulus = dict()
        stimulus['deg_per_cyc'] = random.choice(self.deg_per_cycs[target_port])
        stimulus['orientation'] = random.choice(self.orientations[target_port])
        stimulus['drift_frequency'] = random.choice(self.drift_frequencies[target_port])
        stimulus['phase'] = random.choice(self.phases[target_port])
        stimulus['contrast'] = random.choice(self.contrasts[target_port])
        stimulus['duration'] = random.choice(self.durations[target_port])
        stimulus['location'] = random.choice(self.locations[target_port])
        stimulus['radius'] = random.choice(self.radii[target_port])
        stimulus['H'] = H
        stimulus['W'] = W
        stimulus['Hz'] = Hz

        trial_record['chosen_stim'] = stimulus

        frames_total = round(Hz*stimulus['duration'])

        port_details = {}
        port_details['request_port'] = request_port
        port_details['target_port'] = target_port
        port_details['distractor_port'] = distractor_port

        return stimulus, resolution, frames_total, port_details

    def choose_resolution(self, station, **kwargs):
        H = 1080
        W = 1920
        Hz = 60
        return (H,W,Hz)

    def _setup_phases(self, trial_record, station, subject, **kwargs):
        """
        GratingsAFC:_setup_phases
        1. Pre-trial: gray screen. REQUEST_PORT -> 2
        2. Stimulus: Grating stimulus. RESPONSE_PORT==TARGET_PORT -> CORRECT, else PUNISH
        3. Correct: Give reward
        4. Punish: Timeout
        5. ITI: Gray screen of duration iti,
        """
        (stimulus_details,resolution,frames_total,port_details) = self.calc_stim(trial_record=trial_record, station=station)
        hz = resolution[2]
        if port_details['target_port'] == 'left_port':
            reward_valve = 'left_valve'
        elif port_details['target_port'] == 'right_port':
            reward_valve = 'right_valve'
        elif port_details['target_port'] == 'center_port':
            reward_valve = 'center_valve'

        if stimulus_details['duration']==float('inf'):
            do_post_discrim_stim = False
        else:
            do_post_discrim_stim = True

        self._Phases = []

        reward_size, request_reward_size, ms_penalty, ms_reward_sound, ms_penalty_sound = self.reinforcement_manager.calculate_reinforcement(subject=subject)
        reward_size = np.round(reward_size/1000*60)
        request_reward_size = np.round(request_reward_size/1000*60)
        penalty_size = np.round(ms_penalty/1000*60)
        if do_post_discrim_stim:
            self._Phases.append(ps.PhaseSpec(
                phase_number=0,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                stimulus_details=None,
                transitions={port_details['request_port']: 2},
                frames_until_transition=float('inf'),
                auto_trigger=False,
                phase_type='pre-request',
                phase_name='pre-request',
                hz=hz,
                sounds_played=(station._sounds['trial_start_sound'], 0.050)))
            self._Phases.append(ps.PhaseSpec(
                phase_number=1,
                stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],mask='gauss',ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',autoLog=False),
                stimulus_update_fn=AFCGratings.update_stimulus,
                stimulus_details=stimulus_details,
                transitions={None: 3, port_details['target_port']: 4, port_details['distractor_port']: 5},
                frames_until_transition=frames_total,
                auto_trigger=False,
                phase_type='stimulus',
                phase_name='stim',
                hz=hz,
                sounds_played=(station._sounds['stim_start_sound'], 0.050)))
            self._Phases.append(ps.PhaseSpec(
                phase_number=2,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                stimulus_details=None,
                transitions={port_details['target_port']: 4, port_details['distractor_port']: 5},
                frames_until_transition=float('inf'),
                auto_trigger=False,
                phase_type='post-stimulus',
                phase_name='post-stim',
                hz=hz,
                sounds_played=None))
            self._Phases.append(ps.RewardPhaseSpec(
                phase_number=3,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                stimulus_details=None,
                transitions={None: 6},
                frames_until_transition=reward_size,
                auto_trigger=False,
                phase_type='reinforcement',
                phase_name='reward',
                hz=hz,
                sounds_played=(station._sounds['correct_sound'], ms_reward_sound/1000),
                reward_valve=reward_valve))
            self._Phases.append(ps.PunishmentPhaseSpec(
                phase_number=4,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=(0.,0.,0.,),autoLog=False),
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                stimulus_details=None,
                transitions={None: 6},
                frames_until_transition=penalty_size,
                auto_trigger=False,
                phase_type='reinforcement',
                phase_name='punishment',
                hz=hz,
                sounds_played=(station._sounds['punishment_sound'],ms_penalty_sound/1000)))
            self._Phases.append(ps.PhaseSpec(
                phase_number=5,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_details=None,
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                transitions=None,
                frames_until_transition=round(self.iti*hz),
                auto_trigger=False,
                phase_type='inter-trial',
                phase_name='inter-trial',
                hz=hz,
                sounds_played=(station._sounds['trial_end_sound'], 0.050)))
        else:
            self._Phases.append(ps.PhaseSpec(
                phase_number=1,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                stimulus_details=None,
                transitions={port_details['request_port']: 2},
                frames_until_transition=float('inf'),
                auto_trigger=False,
                phase_type='pre-request',
                phase_name='pre-request',
                hz=hz,
                sounds_played=(station._sounds['trial_start_sound'], 0.050)))
            self._Phases.append(ps.PhaseSpec(
                phase_number=2,
                stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],mask='gauss',ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',autoLog=False),
                stimulus_update_fn=AFCGratings.update_stimulus,
                stimulus_details=stimulus_details,
                transitions={port_details['target_port']: 3, port_details['distractor_port']: 4},
                frames_until_transition=float('inf'),
                auto_trigger=False,
                phase_type='stimulus',
                phase_name='stim',
                hz=hz,
                sounds_played=(station._sounds['stim_start_sound'], 0.050)))
            self._Phases.append(ps.RewardPhaseSpec(
                phase_number=3,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                stimulus_details=None,
                transitions={None: 5},
                frames_until_transition=reward_size,
                auto_trigger=False,
                phase_type='reinforcement',
                phase_name='reward',
                hz=hz,
                sounds_played=(station._sounds['correct_sound'], ms_reward_sound/1000),
                reward_valve=reward_valve))
            self._Phases.append(ps.PunishmentPhaseSpec(
                phase_number=4,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=(0,0,0,),autoLog=False),
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                stimulus_details=None,
                transitions={None: 5},
                frames_until_transition=penalty_size,
                auto_trigger=False,
                phase_type='reinforcement',
                phase_name='punishment',
                hz=hz,
                sounds_played=(station._sounds['punishment_sound'],ms_penalty_sound/1000)))
            self._Phases.append(ps.PhaseSpec(
                phase_number=5,
                stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
                stimulus_details=None,
                stimulus_update_fn=AFCGratings.do_nothing_to_stim,
                transitions=None,
                frames_until_transition=round(self.iti*hz),
                auto_trigger=False,
                phase_type='inter-trial',
                phase_name='inter-trial',
                hz=hz,
                sounds_played=(station._sounds['trial_end_sound'], 0.050)))

    @staticmethod
    def station_ok_for_tm(station):
        if station.__class__.__name__ in ['StandardVisionBehaviorStation','StandardKeyboardStation']:
            return True
        else:
            return False

    @staticmethod
    def trial_compiler(compiled_record, trial_record):
        print('GRATINGSGOONLY:TRIAL_COMPILER::compiling trial')

        try:
            import pprint
            ppr = pprint.PrettyPrinter(indent=4).pprint
            ppr(compiled_record)
            compiled_details = compiled_record['compiled_details']['GratingsGoOnly']
        except KeyError as e:
            traceback.print_stack()
            compiled_details = {}
            compiled_details['trial_number'] = []
            compiled_details['deg_per_cyc'] = []
            compiled_details['orientation'] = []
            compiled_details['drift_frequency'] = []
            compiled_details['phase'] = []
            compiled_details['contrast'] = []
            compiled_details['duration'] = []
            compiled_details['radius'] = []
            # compiled_details['radius_type'] = []
            compiled_details['location'] = []
            compiled_details['H'] = []
            compiled_details['W'] = []
            compiled_details['Hz'] = []
            # put an empty compiled_details in the compiled_records
            compiled_record['compiled_details']['Gratings'] = compiled_details

        compiled_details['trial_number'].append(trial_record['trial_number'])
        compiled_details['deg_per_cyc'].append(trial_record['chosen_stim']['deg_per_cyc'])
        compiled_details['orientation'].append(trial_record['chosen_stim']['orientation'])
        compiled_details['drift_frequency'].append(trial_record['chosen_stim']['drift_frequency'])
        compiled_details['phase'].append(trial_record['chosen_stim']['phase'])
        compiled_details['contrast'].append(trial_record['chosen_stim']['contrast'])
        compiled_details['duration'].append(trial_record['chosen_stim']['duration'])
        compiled_details['radius'].append(trial_record['chosen_stim']['radius'])
        compiled_details['radius_type'].append('None')
        compiled_details['location'].append(trial_record['chosen_stim']['location'])
        compiled_details['H'].append(trial_record['chosen_stim']['H'])
        compiled_details['W'].append(trial_record['chosen_stim']['W'])
        compiled_details['Hz'].append(trial_record['chosen_stim']['Hz'])

        compiled_record['compiled_details'] = compiled_details

        return compiled_details


class GratingsGoOnly(btm.BaseTrialManager):
    """
        GRATINGSGOONLY defines a standard gratings trial manager for Go-No-Go trials. Requires:
            deg_per_cycs
            orientations
            drift_frequencies
            phases
            contrasts
            durations
            radii # in units of "Scale"
            locations

            do_combos
            reinforcement_manager

            VERSION HISTORY:
            0.0.1 : Initial design
            0.0.2 : (1) itl and iti sent to BTM and (2) _setup_phases()
                    are zero-indexed
    """

    def __init__(self,
                 name = 'DemoGratingsGoOnlyTrialManager',
                 deg_per_cycs = [10],
                 orientations = [-np.pi/4],
                 drift_frequencies = [0],
                 phases = np.linspace(start=-np.pi,stop=np.pi,num=8,endpoint=True),
                 contrasts = [1.],
                 durations = [2.],
                 locations = [(0.5,0.5)],
                 radii = [40],
                 iti = 1.,
                 itl = 0.,
                 do_combos = True,
                 delay_distribution = ('Constant',2.),
                 reinforcement_manager = reinfmgr.ConstantReinforcement(),
                 **kwargs):
        super(GratingsGoOnly,self).__init__(iti=iti, itl=itl)
        self.ver = Ver('0.0.2')
        self.name = name
        self.reinforcement_manager = reinforcement_manager

        self.do_combos = do_combos
        self.deg_per_cycs = deg_per_cycs
        self.orientations = orientations
        self.drift_frequencies = drift_frequencies
        self.phases = phases
        self.contrasts = contrasts
        self.durations = durations
        self.locations = locations
        self.radii = radii

        self.delay_distribution = delay_distribution

        self._verify_params_ok()

    def _verify_params_ok(self):
        if self.do_combos:
            # if do_combos, don't have to worry about the lengths of each values
            pass
        else:
            num_options = len(self.deg_per_cycs)
            assert len(self.orientations)==num_options,'orientations not same length as deg_per_cycs'
            assert len(self.drift_frequencies)==num_options,'drift_frequencies not same length as deg_per_cycs'
            assert len(self.phases)==num_options,'phases not same length as deg_per_cycs'
            assert len(self.contrasts)==num_options,'contrasts not same length as deg_per_cycs'
            assert len(self.durations)==num_options,'durations not same length as deg_per_cycs'
            assert len(self.locations)==num_options,'locations not same length as deg_per_cycs'
            assert len(self.radii)==num_options,'radii not same length as deg_per_cycs'

        assert np.logical_and(np.all(np.asarray(self.durations)>0), np.all(np.asarray(self.durations)<float('inf'))), 'All durations should be positive and finite'
        assert self.delay_distribution[0] in ['Constant', 'Uniform', 'Gaussian', 'FlatHazard'], 'what delay distributoin are you using?'

    def __repr__(self):
        return "GRATINGSGOONLY object"

    @staticmethod
    def update_stimulus(stimulus,details):
        if details['drift_frequency'] !=0:
            stimulus.phase += float(details['drift_frequency'])/float(details['Hz'])

    def sample_delay(self):
        if self.delay_distribution[0]=='Constant':
            return self.delay_distribution[1]
        elif self.delay_distribution[0]=='Uniform':
            lo = self.delay_distribution[1][0]
            hi = self.delay_distribution[1][1]
            return np.abs(np.random.uniform(low=lo,high=hi))
        elif self.delay_distribution[0]=='Gaussian':
            mu = self.delay_distribution[1][0]
            sd = self.delay_distribution[1][1]
            return np.abs(np.random.normal(loc=mu,scale=sd)) # returning absolute values
        elif self.delay_distribution[0]=='FlatHazard':
            pctile = self.delay_distribution[1][0]
            val = self.delay_distribution[1][1]
            fixed = self.delay_distribution[1][2]
            max = self.delay_distribution[1][3]
            p = -val/np.log(1-pctile)
            delay = fixed+np.random.exponential(p)
            if delay>max: delay=max
            return delay

    @staticmethod
    def station_ok_for_tm(station):
        if station.__class__.__name__ in ['StandardKeyboardStation','StandardVisionHeadfixStation']:
            return True
        else:
            return False

    def do_trial(self, station, subject, trial_record, compiled_record,quit):
        # returns quit and trial_record
        # resetup the window according to the itl

        # check if okay to run the trial manager with the station
        if not self.station_ok_for_tm(station):
            print('GRATINGSGOONLY:DO_TRIAL: station not ok for tm')
            quit = True
            trial_record['correct'] = None
            trial_record['errored_out'] = True
            return trial_record,quit


        ## _setup_phases
        self._setup_phases(trial_record=trial_record, station=station,compiled_record=compiled_record, subject=subject)
        station._key_pressed = []

        trial_record,quit = super(GratingsGoOnly,self).do_trial(station=station, subject=subject, trial_record=trial_record, compiled_record=compiled_record, quit=quit)
        return trial_record,quit

    def choose_resolution(self, station, **kwargs):
        H = 1080
        W = 1920
        Hz = 60
        return (H,W,Hz)

    def calc_stim(self, trial_record, station, **kwargs):
        (H, W, Hz) = self.choose_resolution(station=station, **kwargs)
        resolution = (H,W,Hz)

        # select from values
        if self.do_combos:
            stimulus_details = dict()
            stimulus_details['deg_per_cyc'] = random.choice(self.deg_per_cycs)
            stimulus_details['orientation'] = random.choice(self.orientations)
            stimulus_details['drift_frequency'] = random.choice(self.drift_frequencies)
            stimulus_details['phase'] = random.choice(self.phases)
            stimulus_details['contrast'] = random.choice(self.contrasts)
            stimulus_details['duration'] = random.choice(self.durations)
            stimulus_details['location'] = random.choice(self.locations)
            stimulus_details['radius'] = random.choice(self.radii)
        else:
            RuntimeError('Not implemented')
        stimulus_details['H'] = H
        stimulus_details['W'] = W
        stimulus_details['Hz'] = Hz

        delay_frame_num = np.round(self.sample_delay()*Hz)
        stimulus_details['delay_frame_num'] = delay_frame_num

        trial_record['chosen_stim'] = stimulus_details

        port_details = {}
        port_details['target_ports'] = 'response_port'
        port_details['distractor_ports'] = None


        return stimulus_details, resolution, port_details, delay_frame_num

    def _setup_phases(self, trial_record, station, subject, **kwargs):
        """
        GratingsGoOnly:_setupPhases follows:
            1. Delay Phase with duration sampled from delay_distribution
            2. ResponsePhase with a GO sound with stimulus being gratings.
            3    a. Response during response duration -> reward
                 b. No response during response duration -> error sound
            4. ITL
        """
        (stimulus_details,resolution,port_details,delay_frame_num) = self.calc_stim(trial_record=trial_record, station=station)
        hz = resolution[2]
        reward_size, request_reward_size, ms_penalty, ms_reward_sound, ms_penalty_sound = self.reinforcement_manager.calculate_reinforcement(subject=subject)
        reward_size = np.round(reward_size/1000.*hz)
        penalty_size = np.round(ms_penalty/1000.*hz)
        iti_size = np.round(self.iti*hz)
        response_frame_num = round(hz*stimulus_details['duration'])

        self._Phases = []
        # Just display stim
        do_nothing = ()

        # sounds
        go_sound = station._sounds['go_sound']
        go_sound.secs = 0.1
        go_sound.seek(0.)
        go_sound.status = NOT_STARTED
        reward_sound = station._sounds['reward_sound']
        reward_sound.secs = ms_reward_sound/1000.
        reward_sound.seek(0.)
        reward_sound.status = NOT_STARTED
        punishment_sound = station._sounds['punishment_sound']
        punishment_sound.seek(0.)
        punishment_sound.status = NOT_STARTED


        # deal with the phases
        # delay phase
        self._Phases.append(ps.PhaseSpec(
            phase_number=0,
            stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
            stimulus_update_fn=btm.BaseTrialManager.do_nothing_to_stim,
            stimulus_details=None,
            transitions={do_nothing: 1},
            frames_until_transition=delay_frame_num,
            auto_trigger=False,
            phase_type='stimulus',
            phase_name='delay_phase',
            hz=hz,
            sounds_played=None))

        # response phase
        self._Phases.append(ps.StimPhaseSpec(
            phase_number=1,
            stimulus=psychopy.visual.GratingStim(win=station._window,tex='sin',sf=stimulus_details['deg_per_cyc'],size=stimulus_details['radius'],ori=stimulus_details['orientation'],phase=stimulus_details['phase'],contrast=stimulus_details['contrast'],units='deg',mask=None,autoLog=False),
            stimulus_update_fn=GratingsGoOnly.update_stimulus,
            stimulus_details=stimulus_details,
            transitions={port_details['target_ports']: 2, do_nothing: 3},
            frames_until_transition=response_frame_num,
            auto_trigger=False,
            phase_type='stimulus',
            phase_name='delay-stim',
            hz=hz,
            sounds_played=[go_sound]))

        # reward phase spec
        self._Phases.append(ps.RewardPhaseSpec(
            phase_number=2,
            stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
            stimulus_details=None,
            stimulus_update_fn=btm.BaseTrialManager.do_nothing_to_stim,
            transitions={do_nothing: 4},
            frames_until_transition=reward_size,
            auto_trigger=False,
            phase_type='reinforcement',
            phase_name='reward_phase',
            hz=hz,
            sounds_played=[reward_sound],
            reward_valve='reward_valve'))

        # punishment phase spec
        self._Phases.append(ps.PunishmentPhaseSpec(
            phase_number=3,
            stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
            stimulus_details=None,
            stimulus_update_fn=btm.BaseTrialManager.do_nothing_to_stim,
            transitions={do_nothing: 4},
            frames_until_transition=penalty_size,
            auto_trigger=False,
            phase_type='reinforcement',
            phase_name='punishment_phase',
            hz=hz,
            sounds_played=[punishment_sound]))

        # itl
        self._Phases.append(ps.PhaseSpec(
            phase_number=4,
            stimulus=psychopy.visual.Rect(win=station._window,width=station._window.size[0],height=station._window.size[1],fillColor=self.itl,autoLog=False),
            stimulus_details=None,
            stimulus_update_fn=btm.BaseTrialManager.do_nothing_to_stim,
            transitions=None,
            frames_until_transition=iti_size,
            auto_trigger=False,
            phase_type='inter-trial',
            phase_name='iti_phase',
            hz=hz,
            sounds_played=None))

    @staticmethod
    def trial_compiler(compiled_record, trial_record):
        print('GRATINGSGOONLY:TRIAL_COMPILER::compiling trial')

        try:
            compiled_details = compiled_record['compiled_details']['GratingsGoOnly']
        except KeyError as e:
            traceback.print_stack()
            compiled_details = {}
            compiled_details['trial_number'] = []
            compiled_details['deg_per_cyc'] = []
            compiled_details['orientation'] = []
            compiled_details['drift_frequency'] = []
            compiled_details['phase'] = []
            compiled_details['contrast'] = []
            compiled_details['duration'] = []
            compiled_details['location'] = []
            compiled_details['radius'] = []
            # compiled_details['radius_type'] = []
            compiled_details['location'] = []
            compiled_details['H'] = []
            compiled_details['W'] = []
            compiled_details['Hz'] = []
            # put an empty compiled_details in the compiled_records
            compiled_record['compiled_details']['GratingsGoOnly'] = compiled_details

        compiled_details['trial_number'].append(trial_record['trial_number'])
        compiled_details['deg_per_cyc'].append(trial_record['chosen_stim']['deg_per_cyc'])
        compiled_details['orientation'].append(trial_record['chosen_stim']['orientation'])
        compiled_details['drift_frequency'].append(trial_record['chosen_stim']['drift_frequency'])
        compiled_details['phase'].append(trial_record['chosen_stim']['phase'])
        compiled_details['contrast'].append(trial_record['chosen_stim']['contrast'])
        compiled_details['duration'].append(trial_record['chosen_stim']['duration'])
        compiled_details['radius'].append(trial_record['chosen_stim']['radius'])
        compiled_details['radius_type'].append('None')
        compiled_details['location'].append(trial_record['chosen_stim']['location'])
        compiled_details['H'].append(trial_record['chosen_stim']['H'])
        compiled_details['W'].append(trial_record['chosen_stim']['W'])
        compiled_details['Hz'].append(trial_record['chosen_stim']['Hz'])

        compiled_record['compiled_details'] = compiled_details

        return compiled_details



if __name__=='__main__':
    g = Gratings_GaussianEdge('SampleGratingsGaussianEdge',
                 deg_per_cycs=[0.01,0.1,1], #cpd?
                 orientations=[-45,-22.5,0,22.5,45], #degrees
                 drift_frequencies=[0,1], #hz
                 phases=[0],
                 contrasts=[1,0.15],
                 durations=[1], #seconds
                 radii=[200], #degrees
                 iti=1, #seconds
                 itl=0., #inter trial luminance
                 )

    g._simulate()
