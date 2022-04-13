#########################################################################
# Purpose: Match jets to partons                                        #
# Author: Jona Bossio (jbossios@cern.ch)                                #
# Date:   21 February 2022                                              #
#########################################################################

import ROOT
import sys
import copy
import logging
from typing import Union, Tuple


class RPVJet(ROOT.TLorentzVector):
    def __init__(self, *args):
        ROOT.TLorentzVector.__init__(self)
        if len(args) == 4:
            self.SetPtEtaPhiE(args[0], args[1], args[2], args[3])
        self.__is_matched = False
        self.__match_type = 'None'  # options: 'None', 'Parton', 'FSR'
        self.__match_parton_index = -1
        self.__match_pdgID = -1
        self.__match_barcode = -1
        self.__match_gluino_barcode = -1
        self.__matched_parton_barcode = -1
        self.__matched_fsr_barcode = -1

    def is_matched(self):
        return self.__is_matched

    def get_match_type(self):
        return self.__match_type

    def get_match_parton_index(self):
        return self.__match_parton_index

    def get_match_pdgid(self):
        return self.__match_pdgid

    def get_match_barcode(self):
        return self.__match_barcode

    def get_match_gluino_barcode(self):
        return self.__match_gluino_barcode

    def set_matched_status(self, status):
        self.__is_matched = status

    def set_match_type(self, match_type):
        self.__match_type = match_type

    def set_match_parton_index(self, index):
        self.__match_parton_index = index

    def set_match_pdgid(self, pdgid):
        self.__match_pdgid = pdgid

    def set_match_barcode(self, barcode):
        self.__match_barcode = barcode

    def set_match_gluino_barcode(self, barcode):
        self.__match_gluino_barcode = barcode

    def set_matched_parton_barcode(self, barcode):
        self.__matched_parton_barcode = barcode

    def get_matched_parton_barcode(self):
        return self.__matched_parton_barcode

    def set_matched_fsr_barcode(self, barcode):
        self.__matched_fsr_barcode = barcode

    def get_matched_fsr_barcode(self):
        return self.__matched_fsr_barcode


class RPVParton(ROOT.TLorentzVector):
    def __init__(self, *args):
        ROOT.TLorentzVector.__init__(self)
        if len(args) == 4:
            self.SetPtEtaPhiE(args[0], args[1], args[2], args[3])
        self.__quark_barcode = -999  # barcode of last quark in chain corresponding to this FSR # noqa
        self.__gluino_barcode = -999  # barcode of corresponding gluino
        self.__barcode = -999  # particle's barcode
        self.__pdgID = -999  # particle's pdg ID

    def set_quark_barcode(self, barcode):
        self.__quark_barcode = barcode

    def get_quark_barcode(self):
        return self.__quark_barcode

    def set_gluino_barcode(self, barcode):
        self.__gluino_barcode = barcode

    def get_gluino_barcode(self):
        return self.__gluino_barcode

    def set_barcode(self, barcode):
        self.__barcode = barcode

    def get_barcode(self):
        return self.__barcode

    def set_pdgid(self, pdgid):
        self.__pdgID = pdgid

    def get_pdgid(self):
        return self.__pdgID


class RPVMatcher():
    __properties_defaults = {
      'MatchingCriteria': 'RecomputeDeltaRvalues_drPriority',  # other options: 'UseFTDeltaRvalues', 'RecomputeDeltaRvalues_drPriority' # noqa
      'DeltaRcut': 0.4,
      'ReturnOnlyMatched': False,
      'Debug': False,
      'DisableNmatchedJetProtection': False,
      'MatchFSRsFromMatchedGluinoDecays': False
    }

    def add_jets(self, jets: [RPVJet]):
        self.__jets = jets

    def add_partons(self, partons: [RPVParton]):
        self.__partons = partons

    def add_fsrs(self, fsrs: [RPVParton]):
        self.__fsrs = fsrs

    def set_property(self, opt: str, value: Union[bool, float]):
        if opt not in self.__properties_defaults:
            self.__log.fatal(f'{opt} was not recognized, exiting')
            sys.exit(1)
        self.__properties[opt] = value

    def debug(self):
        self.set_property('Debug', True)

    def __get_parton_info(self, partons, barcode) -> Tuple:  # -> ("index", "pdgID", "gluino_barcode") # noqa
        """ Get info of quark from gluino matched to a jet """
        # Loop over quarks from gluinos
        for parton_index, parton in enumerate(partons):
            if partons[parton_index].get_barcode() == barcode:
                return (
                  parton_index,
                  partons[parton_index].get_pdgid(),
                  partons[parton_index].get_gluino_barcode()
                )
        self.__log.error(f'Parton with barcode={barcode} not found, exiting')
        sys.exit(1)

    def __get_fsr_info(self, fsrs, barcode) -> Tuple:  # -> ("index", "pdgID", "gluino_barcode", "quark_barcode") # noqa
        """ Get info of FSR quark matched to a jet """
        for fsr_index, fsr in enumerate(fsrs):  # loop over FSRs
            if fsrs[fsr_index].get_barcode() == barcode:
                return (
                  fsr_index,
                  fsrs[fsr_index].get_pdgid(),
                  fsrs[fsr_index].get_gluino_barcode(),
                  fsrs[fsr_index].get_quark_barcode()
                )
        self.__log.error(f'FSR with barcode={barcode} not found, exiting')
        sys.exit(1)

    def __decorate_jet(
            self,
            jet,
            match_type,
            parton_index,
            pdgid,
            barcode,
            gluino_barcode
            ):
        jet.set_matched_status(True)
        jet.set_match_type(match_type)
        jet.set_match_parton_index(parton_index)
        jet.set_match_pdgid(pdgid)
        jet.set_match_barcode(barcode)
        jet.set_match_gluino_barcode(gluino_barcode)

    def __remove_decoration(self, jet):
        jet.set_matched_status(False)
        jet.set_match_type('None')
        jet.set_match_parton_index(-1)
        jet.set_match_pdgid(-1)
        jet.set_match_barcode(-1)
        jet.set_match_gluino_barcode(-1)

    def __get_parton_info_and_decorate_jet(
            self,
            partons,
            jet,
            case,
            info_dict
            ):
        if 'jet_matched_barcode' in info_dict:
            # Jets are matched to partons using FT decisions
            jet_matched_barcode = info_dict['jet_matched_barcode']
            if case == 'Parton':
                self.__matched_partons.append(jet_matched_barcode)
            parton_info = self.__get_parton_info(partons, jet_matched_barcode)
            parton_index, pdgid, gluino_barcode = parton_info
            self.__decorate_jet(
                jet,
                case,
                parton_index,
                pdgid,
                jet_matched_barcode,
                gluino_barcode
                )
        elif 'matched_parton_index' in info_dict:
            # Jets are matched to partons recalculating DeltaR values
            if case == 'Parton':
                self.__matched_partons.append(
                    info_dict['matched_parton_barcode']
                    )
            matched_parton_index = info_dict['matched_parton_index']
            pdgid = partons[matched_parton_index].get_pdgid()
            gluino_barcode = partons[matched_parton_index].get_gluino_barcode()
            self.__decorate_jet(
                jet,
                case,
                matched_parton_index,
                pdgid,
                info_dict['matched_parton_barcode'],
                gluino_barcode
                )

    def __check_fsr_match_and_decorate_jet(self, jet, partons, info_dict):
        """
        If 2 FSRs associated to the same last quark
        in the gluino decay chain are matched,
        match FSR matching the jet w/ highest pt
        or lowest DeltaR depending on config
        (it only matters for calculating true reconstructed masses)
        """
        another_fsr_matches_same_quark_barcode = False
        current_matched_fsrs = copy.deepcopy(self.__matched_fsrs)
        for findex in current_matched_fsrs:
            if current_matched_fsrs[findex]['quark_barcode'] == info_dict['matched_parton_barcode']: # noqa
                # I found another matched FSR from same last quark from gluino
                another_fsr_matches_same_quark_barcode = True
                pt_priority = self.__properties['MatchingCriteria'] != 'RecomputeDeltaRvalues_drPriority' # noqa
                self.__log.debug(f'jet.Pt() = {jet.Pt()}')
                self.__log.debug(f"self.__jets[{current_matched_fsrs[findex]['jet_index']}].Pt() = {self.__jets[current_matched_fsrs[findex]['jet_index']].Pt()}") # noqa
                self.__log.debug(f"self.__jets[{current_matched_fsrs[findex]['jet_index']}].DeltaR(partons[{findex}]) = {self.__jets[current_matched_fsrs[findex]['jet_index']].DeltaR(partons[findex])}") # noqa
                self.__log.debug(f"jet.DeltaR(partons[{info_dict['matched_parton_index']}]) = {jet.DeltaR(partons[info_dict['matched_parton_index']])}") # noqa
                if pt_priority and jet.Pt() < self.__jets[current_matched_fsrs[findex]['jet_index']].Pt(): # noqa
                    pass  # do not match jet_index to matched_parton_index
                elif not pt_priority:
                    if self.__jets[current_matched_fsrs[findex]['jet_index']].DeltaR(partons[findex]) < jet.DeltaR(partons[info_dict['matched_parton_index']]): # noqa
                        pass  # do not match jet_index to matched_parton_index
                else:
                    # unmatch old jet
                    self.__log.debug(f'Jet {current_matched_fsrs[findex]["jet_index"]} is un-matched to FSR {findex} with last quark barcode {current_matched_fsrs[findex]["quark_barcode"]}') # noqa
                    self.__remove_decoration(
                        self.__jets[current_matched_fsrs[findex]['jet_index']]
                        )
                    self.__matched_fsrs.pop(findex)
                    # decorate new matched jet
                    self.__matched_fsrs[info_dict['matched_parton_index']] = {
                        'jet_index': info_dict['jet_index'],
                        'quark_barcode': info_dict['matched_parton_barcode'],
                        }
                    self.__log.debug(f'Jet {info_dict["jet_index"]} is matched to FSR {info_dict["matched_parton_index"]} with last quark barcode {info_dict["matched_parton_barcode"]} [check passed!]') # noqa
                    if 'pdgid' in info_dict:
                        # Jets are matched to partons using FT decisions
                        self.__decorate_jet(
                            jet,
                            'FSR',
                            info_dict['matched_parton_index'],
                            info_dict['pdgid'],
                            info_dict['matched_parton_barcode'],
                            info_dict['gluino_barcode']
                            )
                    else:
                        # Jets are matched to partons remaking decisions
                        self.__get_parton_info_and_decorate_jet(
                            partons=partons,
                            jet=jet,
                            case='FSR',
                            info_dict=info_dict
                            )
        if not another_fsr_matches_same_quark_barcode:
            self.__matched_fsrs[info_dict['matched_parton_index']] = {
              'jet_index': info_dict['jet_index'],
              'quark_barcode': info_dict['matched_parton_barcode']
            }
            self.__log.debug(f'Jet {info_dict["jet_index"]} is matched to FSR {info_dict["matched_parton_index"]} with last quark barcode {info_dict["matched_parton_barcode"]} [check passed!]') # noqa
            if 'pdgid' in info_dict:
                # Jets are matched to partons using FT decisions
                self.__decorate_jet(
                  jet,
                  'FSR',
                  info_dict['matched_parton_index'],
                  info_dict['pdgid'],
                  info_dict['matched_parton_barcode'],
                  info_dict['gluino_barcode']
                )
            else:
                # Jets are matched to partons recalculating DeltaR values
                self.__get_parton_info_and_decorate_jet(
                  partons=partons,
                  jet=jet,
                  case='FSR',
                  info_dict=info_dict
                )

    def __matcher_recompute_deltar_values(self, partons, is_fsr, dr_cut):
        """ Match jets to partons/FSRs re-computing DeltaR values """
        for jet_index, jet in enumerate(self.__jets):  # loop over jets
            if jet.is_matched():
                continue  # skip matched jet
            dr_min = 1E5
            # Loop over partons
            for parton_index, parton in enumerate(partons):
                barcode = parton.get_barcode() if not is_fsr else parton.get_quark_barcode() # noqa
                # Skip matched parton/FSR
                if barcode in self.__matched_partons:
                    properties = self.__properties
                    if not is_fsr:
                        # Always skip matched last-quark in gluino decay chain
                        continue
                    elif not properties['MatchFSRsFromMatchedGluinoDecays']:
                        # skip FSRs associated to matched gluino decay
                        # (unless asked not to)
                        continue
                dr = jet.DeltaR(parton)
                if dr < dr_min:
                    dr_min = dr
                    matched_parton_index = parton_index
                    matched_parton_barcode = barcode
            if dr_min < dr_cut:  # jet is matched
                if is_fsr:
                    self.__log.debug(f'Jet {jet_index} is matched (DeltaR={dr_min}) to FSR {matched_parton_index} with last quark barcode {matched_parton_barcode} [check pending...]') # noqa
                    info_dict = {
                      'jet_index': jet_index,
                      'matched_parton_index': matched_parton_index,
                      'matched_parton_barcode': matched_parton_barcode
                    }
                    self.__check_fsr_match_and_decorate_jet(
                      jet=jet,
                      partons=partons,
                      info_dict=info_dict
                    )
                else:  # not an FSR
                    self.__log.debug(f'Jet {jet_index} is matched (DeltaR={dr_min}) to last quark {matched_parton_index} with barcode {matched_parton_barcode}') # noqa
                    info_dict = {
                      'matched_parton_index': matched_parton_index,
                      'matched_parton_barcode': matched_parton_barcode
                    }
                    self.__get_parton_info_and_decorate_jet(
                      partons=partons,
                      jet=jet,
                      case='Parton',
                      info_dict=info_dict
                    )

    def __matcher_use_deltar_values_from_ft(self, partons, is_fsr):
        """
        Match jets to partons/FSRs
        using already computed DeltaR values from FT
        """
        parton_type = "partons" if not is_fsr else "FSRs"
        self.__log.debug(f'Matching jets to {parton_type} using FT decisions')
        for jet_index, jet in enumerate(self.__jets):  # loop over jets
            if jet.is_matched():
                continue  # skip matched jet
            # Check if jet is matched
            jet_matched_barcode = jet.get_matched_parton_barcode() if not is_fsr else jet.get_matched_fsr_barcode() # noqa
            if jet_matched_barcode != -1:  # make sure jet matches a parton/FSR
                if is_fsr:
                    fsr_info_tuple = self.__get_fsr_info(
                        partons,
                        jet_matched_barcode
                        )
                    fsr_index, pdgid, gluino_barcode, quark_barcode = fsr_info_tuple # noqa
                    self.__log.debug(f'Jet {jet_index} is matched to FSR (barcode={jet_matched_barcode}) with last quark barcode {quark_barcode} [check pending...]') # noqa
                    # Make sure this quark is not already matched
                    if quark_barcode not in self.__matched_partons:
                        self.__log.debug(f'Jet {jet_index} is matched to FSR (barcode={jet_matched_barcode}) with last quark barcode {quark_barcode} [check 1/2 passed!]') # noqa
                        info_dict = {
                          'jet_index': jet_index,
                          'matched_parton_index': fsr_index,
                          'matched_parton_barcode': quark_barcode,
                          'pdgid': pdgid,
                          'gluino_barcode': gluino_barcode
                          }
                        self.__check_fsr_match_and_decorate_jet(
                          jet=jet,
                          partons=partons,
                          info_dict=info_dict
                        )
                    else:
                        self.__log.debug(f"Jet {jet_index} is matched to FSR (barcode={jet_matched_barcode}) with last quark barcode {quark_barcode} [check 1/2 didn't pass!]") # noqa
                else:
                    self.__log.debug(f'Jet {jet_index} is matched to last quark (barcode={jet_matched_barcode})') # noqa
                    info_dict = {'jet_matched_barcode': jet_matched_barcode}
                    self.__get_parton_info_and_decorate_jet(
                      partons=partons,
                      jet=jet,
                      case='Parton',
                      info_dict=info_dict
                    )

    def __get_n_matched_jets(self) -> int:
        """ Get number of matched jets """
        return sum([1 if jet.is_matched() else 0 for jet in self.__jets])

    def __check_n_matched_jets(self):
        """ Exit if more than 6 jets were matched
        (this is a protection, it should never happen) """
        n_matched_jets = self.__get_n_matched_jets()
        if n_matched_jets > 6:
            msg = f'more than 6 ({n_matched_jets}) jets are matched, exiting'
            self.__log.fatal(msg)
            sys.exit(1)

    def __return_jets(self) -> [RPVJet]:
        """
        Return all jets
        or only matched jets
        (depending on configuration)
        """
        if not self.__properties['ReturnOnlyMatched']:
            return self.__jets
        else:
            return [jet for jet in self.__jets if jet.is_matched()]

    def __match_use_deltar_values_from_ft(self) -> [RPVJet]:
        """ Match jets to partons using FT decisions """
        properties = self.__properties
        fsr = ' and FSRs' if self.__fsrs else ''
        msg = f'Jets will be matched to partons{fsr} using FT decisions'
        self.__log.debug(msg)
        case = 'only matched' if properties['ReturnOnlyMatched'] else 'all'
        msg = f'Will return {case} jets'
        self.__log.debug(msg)
        self.__log.debug('Matching partons to jets')
        self.__matcher_use_deltar_values_from_ft(self.__partons, False)
        if self.__fsrs and self.__get_n_matched_jets() < 6:
            self.__log.debug('Matching FSRs to jets')
            self.__matcher_use_deltar_values_from_ft(self.__fsrs, True)
        if not self.__properties['DisableNmatchedJetProtection']:
            self.__check_n_matched_jets()
        return self.__return_jets()

    def __match_recompute_deltar_values(self) -> [RPVJet]:
        """ Match jets to partons recalculating DeltaR values """
        properties = self.__properties
        fsr = ' and FSRs' if self.__fsrs else ''
        cut = properties['DeltaRcut']
        msg = f'Jets will be matched to partons{fsr} using DeltaR_max = {cut}'
        self.__log.debug(msg)
        case = 'only matched' if properties['ReturnOnlyMatched'] else 'all'
        msg = f'Will return {case} jets'
        self.__log.debug(msg)
        self.__matcher_recompute_deltar_values(self.__partons, 0, cut)
        if self.__fsrs and self.__get_n_matched_jets() < 6:
            self.__matcher_recompute_deltar_values(self.__fsrs, 1, cut)
        if not properties['DisableNmatchedJetProtection']:
            self.__check_n_matched_jets()
        return self.__return_jets()

    def __init__(self, **kargs):
        logging.basicConfig(level='INFO', format='%(levelname)s: %(message)s')
        self.__log = logging.getLogger()
        # Protection
        for key in kargs:
            if key not in self.__properties_defaults:
                if key != 'Jets' and key != 'Partons' and key != 'FSRs':
                    self.__log.fatal(f'{key} was not recognized, exiting')
                    sys.exit(1)
        self.__properties = dict()
        # Set default properties
        for opt, default_value in self.__properties_defaults.items():
            self.__properties[opt] = default_value
        # Use provided settings
        if 'Jets' in kargs:
            self.__jets = kargs['Jets']
        else:
            self.__jets = None
        if 'Partons' in kargs:
            self.__partons = kargs['Partons']
        else:
            self.__partons = None
        if 'FSRs' in kargs:
            self.__fsrs = kargs['FSRs']
        else:
            self.__fsrs = None
        for key in kargs:
            if key in self.__properties_defaults:
                self.set_property(key, kargs[key])
        # Protection
        prop = self.__properties
        disable_njet_protection = prop['DisableNmatchedJetProtection']
        match_fsrs_from_matched_gs = prop['MatchFSRsFromMatchedGluinoDecays']
        if match_fsrs_from_matched_gs and not disable_njet_protection:
            self.__log.info('DisableNmatchedJetProtection property has been enabled') # noqa
        self.__matched_partons = []
        self.__matched_fsrs = {}
        self.__functions = {
          'RecomputeDeltaRvalues_ptPriority': self.__match_recompute_deltar_values, # noqa
          'RecomputeDeltaRvalues_drPriority': self.__match_recompute_deltar_values, # noqa
          'UseFTDeltaRvalues': self.__match_use_deltar_values_from_ft,
        }

    def __check_info(self, index, particle, particle_type):
        parton_type = "parton" if particle_type == "Parton" else "FSR"
        if particle_type == 'FSR' and particle.get_quark_barcode() == -999:
            msg = f'quark_barcode not set for {parton_type}_index = {index}'
            self.__log.fatal(msg + ', exiting')
            sys.exit(1)
        if particle. get_gluino_barcode() == -999:
            msg = f'gluino_barcode not set for {parton_type}_index = {index}'
            self.__log.fatal(msg + ', exiting')
            sys.exit(1)
        if particle.get_barcode() == -999:
            msg = f'barcode not set for {parton_type}_index = {index}'
            self.__log.fatal(msg + ', exiting')
            sys.exit(1)
        if particle.get_pdgid() == -999:
            msg = f'pdgid not set for {parton_type}_index = {index}'
            self.__log.fatal(msg + ', exiting')
            sys.exit(1)

    def __check_partons(self, is_fsr):
        if not is_fsr:
            for index, parton in enumerate(self.__partons):
                self.__check_info(index, parton, 'Parton')
        else:  # FSR
            for index, fsr in enumerate(self.__fsrs):
                self.__check_info(index, fsr, 'FSR')

    def match(self) -> [RPVJet]:
        # Protection
        prop = self.__properties
        disable_njet_protection = prop['DisableNmatchedJetProtection']
        match_fsrs_from_matched_gs = prop['MatchFSRsFromMatchedGluinoDecays']
        if match_fsrs_from_matched_gs and not disable_njet_protection:
            self.__log.info('DisableNmatchedJetProtection property has been enabled') # noqa
        # clean up matching decisions if same instance was already used
        self.__matched_partons = []
        self.__matched_fsrs = {}
        if prop['Debug']:
            self.__log.setLevel('DEBUG')
        else:
            self.__log.setLevel('INFO')
        self.__log.debug('Calling match()')
        # Protections
        matching_criteria = prop['MatchingCriteria']
        if matching_criteria not in self.__functions:
            msg = f'MatchingCriteria=={matching_criteria} is not supported'
            self.__log.fatal(msg + ', exiting')
            sys.exit(1)
        default_cut = self.__properties_defaults['DeltaRcut']
        non_default_cut = prop['DeltaRcut'] != default_cut
        if non_default_cut and 'RecomputeDeltaRvalues' not in matching_criteria: # noqa
            msg = 'DeltaRcut set but "RecomputeDeltaRvalues" not in MatchingCriteria' # noqa
            self.__log.fatal(msg + ', exiting')
            sys.exit(1)
        if not self.__jets:
            self.__log.fatal('No jets were provided, exiting')
            sys.exit(1)
        if not self.__partons:
            self.__log.fatal('No partons were provided, exiting')
            sys.exit(1)
        self.__check_partons(False)
        if self.__fsrs:
            self.__check_partons(True)
        # Run appropriate matching
        return self.__functions[matching_criteria]()
