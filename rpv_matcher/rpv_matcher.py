#########################################################################
# Purpose: Match jets to partons                                        #
# Author: Jona Bossio (jbossios@cern.ch)                                #
# Date:   21 February 2022                                              #
#########################################################################

import ROOT
import sys
import copy
import logging
from typing import Union

class RPVJet(ROOT.TLorentzVector):
  def __init__(self, *args):
    ROOT.TLorentzVector.__init__(self)
    if len(args) == 4:
      self.SetPtEtaPhiE(args[0], args[1], args[2], args[3])
    self.__is_matched = False
    self.__match_type = 'None' # options: 'None', 'Parton', 'FSR'
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
    self.quark_barcode = -999 # barcode of last quark in chain corresponding to this FSR
    self.gluino_barcode = -999 # barcode of corresponding gluino
    self.barcode = -999 # particle's barcode
    self.pdgID = -999 # particle's pdg ID

  def set_quark_barcode(self, barcode):
    self.quark_barcode = barcode
  def get_quark_barcode(self):
    return self.quark_barcode

  def set_gluino_barcode(self, barcode):
    self.gluino_barcode = barcode
  def get_gluino_barcode(self):
    return self.gluino_barcode

  def set_barcode(self, barcode):
    self.barcode = barcode
  def get_barcode(self):
    return self.barcode

  def set_pdgid(self, pdgid):
    self.pdgID = pdgid
  def get_pdgid(self):
    return self.pdgID

class RPVMatcher():
  __properties = {
    'MatchingCriteria': 'RecomputeDeltaRvalues', # other options: 'UseFTDeltaRvalues'
    'DeltaRcut' : 0.4,
    'ReturnOnlyMatched' : False,
    'Debug': False,
  }
  def add_jets(self, jets: [RPVJet]):
    self.jets = jets

  def add_partons(self, partons: [RPVParton]):
    self.partons = partons

  def add_fsrs(self, fsrs: [RPVParton]):
    self.fsrs = fsrs

  def set_property(self, opt: str, value: Union[bool, float]):
    if opt not in self.__properties:
      self.__log.fatal(f'{opt} was not recognized, exiting')
      sys.exit(1)
    self.properties[opt] = value

  def debug(self):
    set_property('Debug', True)

  def __get_parton_info(self, partons, barcode) -> ("index", "pdgID", "gluino_barcode"):
    """ Get info of quark from gluino matched to a jet """
    # Loop over quarks from gluinos
    for parton_index, parton in enumerate(partons):
      if partons[parton_index].barcode == barcode:
        return parton_index, partons[parton_index].get_pdgid(), partons[parton_index].get_gluino_barcode()
    return -1,-1,-1

  def __get_fsr_info(self, fsrs, barcode) -> ("index", "pdgID", "gluino_barcode", "quark_barcode"):
    """ Get info of FSR quark matched to a jet """
    for fsr_index, fsr in enumerate(fsrs): # loop over FSRs
      if fsrs[fsr_index].barcode == barcode:
        return fsr_index, fsrs[fsr_index].get_pdgid(), fsrs[fsr_index].get_gluino_barcode(), fsrs[fsr_index].get_quark_barcode()
    return -1,-1,-1,-1

  def __decorate_jet(self, jet, match_type, parton_index, pdgid, barcode, gluino_barcode):
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

  def __matcher_recompute_deltar_values(self, partons, is_fsr, dr_cut):
    """ Match jets to partons/FSRs re-computing DeltaR values """
    for jet_index, jet in enumerate(self.jets): # loop over jets
      if jet.is_matched(): continue # skip matched jet
      matched_parton_barcode = -1
      dr_min = 1E5
      for parton_index, parton in enumerate(partons): # loop over partons
        barcode = parton.get_barcode() if not is_fsr else parton.get_quark_barcode()
        if barcode in self.matched_partons: continue # skip matched parton/FSR
        # FIXME TODO skip already matched FSRs
        # If two FSRs corresponding to the same last quark in the gluino decay chain are matched, match FSR matching the jet w/ highest pt (it only matters for calculating true reconstructed masses)
        dr = jet.DeltaR(parton)
        if dr < dr_min:
          dr_min = dr
          matched_parton_index = parton_index
          matched_parton_barcode = barcode
      if dr_min < dr_cut: # jet is matched
        self.matched_partons.append(matched_parton_barcode)
        pdgid = partons[matched_parton_index].get_pdgid()
        barcode = partons[matched_parton_index].get_barcode()
        gluino_barcode = partons[matched_parton_index].get_gluino_barcode()
        self.__decorate_jet(jet, 'FSR' if is_fsr else 'Parton', matched_parton_index, pdgid, barcode, gluino_barcode)

  def __matcher_use_deltar_values_from_ft(self, partons, is_fsr):
    """ Match jets to partons/FSRs using already computed DeltaR values from FT """
    self.__log.debug(f'Matching jets to {"partons" if not is_fsr else "FSRs"} using already computed DeltaR values from FT')
    for jet_index, jet in enumerate(self.jets): # loop over jets
      if jet.is_matched(): continue # skip matched jet
      # Check if jet is matched
      jet_matched_barcode = jet.get_matched_parton_barcode() if not is_fsr else jet.get_matched_fsr_barcode()
      if jet_matched_barcode != -1: # make sure jet matches a parton/FSR
        if not is_fsr: # get parton's info
          parton_index, pdgid, gluino_barcode = self.__get_parton_info(partons, jet_matched_barcode)
          self.matched_partons.append(jet_matched_barcode)
          self.__log.debug(f'Decorating jet ({jet_index}) matched to a parton ({parton_index})')
          self.__decorate_jet(jet, 'Parton', parton_index, pdgid, jet_matched_barcode, gluino_barcode)
        else: # get FSR's info
          fsr_index, pdgid, gluino_barcode, quark_barcode = self.__get_fsr_info(partons, jet_matched_barcode)
          if quark_barcode not in self.matched_partons: # make sure this quark is not already matched
            self.__log.debug(f'Jet index {jet_index} is temporarily matched to FSR with index {fsr_index}')
            self.__log.debug(f'{quark_barcode = }')
            self.__log.debug(f'{self.matched_partons = }')
            # If two FSRs corresponding to the same last quark in the gluino decay chain are matched, match FSR matching the jet w/ highest pt (it only matters for calculating true reconstructed masses)
            another_fsr_matches_same_quark_barcode = False
            current_matched_fsrs = copy.deepcopy(self.matched_fsrs)
            for findex in current_matched_fsrs:
              if current_matched_fsrs[findex]['quark_barcode'] == quark_barcode: # found another matched FSR from same quark from gluino
                another_fsr_matches_same_quark_barcode = True
                if partons[findex].Pt() > partons[fsr_index].Pt():
                  self.__log.debug(f'Jet index {jet_index} will not be matched to FSR with index {fsr_index}')
                  another_fsr_matches_same_quark_barcode = True
                  pass # skip this FSR
                else:
                  self.__log.debug(f'Jet index {jet_index} will be matched to FSR with index {fsr_index} and jet ({current_matched_fsrs[findex]["jet_index"]}) will be unmatched')
                  # unmatch old jet
                  self.__remove_decoration(self.jets[current_matched_fsrs[findex]['jet_index']])
                  self.matched_fsrs.pop(findex)
                  # decorate new matched jet
                  self.matched_fsrs[fsr_index] = {
                    'jet_index' : jet_index,
                    'quark_barcode': quark_barcode,
                  }
                  self.__decorate_jet(jet, 'FSR', fsr_index, pdgid, jet_matched_barcode, gluino_barcode)
            if not another_fsr_matches_same_quark_barcode:
              self.__log.debug(f'Jet index {jet_index} is matched to FSR with index {fsr_index}')
              self.matched_fsrs[fsr_index] = {
                'jet_index' : jet_index,
                'quark_barcode': quark_barcode,
              }
              self.__decorate_jet(jet, 'FSR', fsr_index, pdgid, jet_matched_barcode, gluino_barcode)

  def __check_n_matched_jets(self):
    n_matched_jets = sum([1 if jet.is_matched() else 0 for jet in self.jets])
    if n_matched_jets > 6:
      self.__log.fatal('more than 6 ({}) jets are matched, exiting'.format(n_matched_jets))
      sys.exit(1)

  def __return_jets(self):
    return self.jets if not self.properties['ReturnOnlyMatched'] else [jet for jet in self.jets if jet.is_matched()]

  def __match_use_deltar_values_from_ft(self) -> [RPVJet]:
    self.__log.debug('Jets will be matched to partons{} using DeltaR values from FactoryTools'.format(' and FSRs' if self.fsrs else ''))
    self.__log.debug('Will return {} jets'.format('only matched' if self.properties['ReturnOnlyMatched'] else 'all'))
    self.__log.debug('Matching partons to jets')
    self.__matcher_use_deltar_values_from_ft(self.partons, False)
    if self.fsrs:
      self.__log.debug('Matching FSRs to jets')
      self.__matcher_use_deltar_values_from_ft(self.fsrs, True)
    self.__check_n_matched_jets()
    return self.__return_jets()

  def __match_recompute_deltar_values(self) -> [RPVJet]:
    self.__log.debug('Jets will be matched to partons{} computing DeltaR values using a maximum DeltaR value of {}'.format(' and FSRs' if self.fsrs else '', self.properties['DeltaRcut']))
    self.__log.debug('Will return {} jets'.format('only matched' if self.properties['ReturnOnlyMatched'] else 'all'))
    self.__matcher_recompute_deltar_values(self.partons, False, self.properties['DeltaRcut'])
    if self.fsrs: self.__matcher_recompute_deltar_values(self.fsrs, True, self.properties['DeltaRcut'])
    self.__check_n_matched_jets()
    return self.__return_jets()

  def __init__(self, **kargs):
    logging.basicConfig(level = 'INFO', format = '%(levelname)s: %(message)s')
    self.__log = logging.getLogger()
    # Protection
    for key in kargs:
      if key not in self.__properties and key != 'Jets' and key != 'Partons' and key != 'FSRs':
        self.__log.fatal(f'{opt} was not recognized, exiting')
        sys.exit(1)
    self.properties = dict()
    # Set default properties
    for opt, default_value in self.__properties.items():
      self.properties[opt] = default_value
    # Use provided settings
    if 'Jets' in kargs:
      self.jets = kargs['Jets']
    else:
      self.jets = None
    if 'Partons' in kargs:
      self.partons = kargs['Partons']
    else:
      self.partons = None
    if 'FSRs' in kargs:
      self.fsrs = kargs['FSRs']
    else:
      self.fsrs = None
    for key in kargs:
      if key in self.__properties:
        self.set_property(key, kargs[key])
    self.matched_partons = []
    self.matched_fsrs = {}
    self.__functions = {
      'RecomputeDeltaRvalues' : self.__match_recompute_deltar_values,
      'UseFTDeltaRvalues': self.__match_use_deltar_values_from_ft,
    }

  def __check_info(self, index, particle, particle_type):
    if particle_type == 'FSR' and particle.get_quark_barcode() == -999:
      self.__log.fatal(f'quark_barcode not set for {"parton" if particle_type == "Parton" else "FSR"}_index = {index}, exiting')
      sys.exit(1)
    if particle. get_gluino_barcode() == -999:
      self.__log.fatal(f'gluino_barcode not set for {"parton" if particle_type == "Parton" else "FSR"}_index = {index}, exiting')
      sys.exit(1)
    if particle.get_barcode() == -999:
      self.__log.fatal(f'barcode not set for {"parton" if particle_type == "Parton" else "FSR"}_index = {index}, exiting')
      sys.exit(1)
    if particle.get_pdgid() == -999:
      self.__log.fatal(f'pdgid not set for {"parton" if particle_type == "Parton" else "FSR"}_index = {index}, exiting')
      sys.exit(1)

  def __check_partons(self, is_fsr):
    if not is_fsr:
      for index, parton in enumerate(self.partons):
        self.__check_info(index, parton, 'Parton')
    else: # FSR
      for index, fsr in enumerate(self.fsrs):
        self.__check_info(index, fsr, 'FSR')

  def match(self) -> [RPVJet]:
    # clean up matching decisions if same instance was already used
    self.matched_partons = []
    self.matched_fsrs = {}
    if self.properties['Debug']: self.__log.setLevel('DEBUG')
    self.__log.debug('Calling match()')
    # Protections
    if self.properties['MatchingCriteria'] not in self.__functions:
      self.__log.fatal(f'MatchingCriteria=={self.properties["MatchingCriteria"]} is not supported, exiting')
      sys.exit(1)
    if self.properties['DeltaRcut'] != self.__properties['DeltaRcut'] and self.properties['MatchingCriteria'] != 'RecomputeDeltaRvalues':
      self.__log.fatal('DeltaRcut was set but MatchingCriteria != "RecomputeDeltaRvalues", exiting')
      sys.exit(1)
    if not self.jets:
      self.__log.fatal('No jets were provided, exiting')
      sys.exit(1)
    if not self.partons:
      self.__log.fatal('No partons were provided, exiting')
      sys.exit(1)
    self.__check_partons(False)
    if self.fsrs: self.__check_partons(True)
    # Run appropriate matching
    return self.__functions[self.properties['MatchingCriteria']]()
