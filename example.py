from ATLAS_SUSY_RPVMJ_JetPartonMatcher.rpv_matcher import RPVJet
from ATLAS_SUSY_RPVMJ_JetPartonMatcher.rpv_matcher import RPVParton
from ATLAS_SUSY_RPVMJ_JetPartonMatcher.rpv_matcher import RPVMatcher

# Construct jets
selected_jets = [RPVJet(), RPVJet(), RPVJet()]
selected_jets[0].SetPtEtaPhiE(35,0,1.2,20)
selected_jets[0].set_matched_parton_barcode(1)
selected_jets[1].SetPtEtaPhiE(25,0,0.25,25)
selected_jets[1].set_matched_parton_barcode(2)
selected_jets[2].SetPtEtaPhiE(23,0,0.01,23)
selected_jets[2].set_matched_parton_barcode(-1)
selected_jets[2].set_matched_fsr_barcode(1)

# Construct partons
partons = [RPVParton(), RPVParton()]
partons[0].SetPtEtaPhiE(30,0,1.3,15)
partons[0].set_gluino_barcode(1)
partons[0].set_barcode(1)
partons[0].set_pdgid(1)
partons[1].SetPtEtaPhiE(20,0,0.2,20)
partons[1].set_gluino_barcode(1)
partons[1].set_barcode(2)
partons[1].set_pdgid(3)

# Construct FSRs
fsrs = [RPVParton()]
fsrs[0].SetPtEtaPhiE(22,0,0.02,22)
fsrs[0].set_quark_barcode(3)
fsrs[0].set_gluino_barcode(1)
fsrs[0].set_barcode(1)
fsrs[0].set_pdgid(1)

matcher = RPVMatcher(Jets = selected_jets, Partons = partons, FSRs = fsrs)
matcher.set_property('ReturnOnlyMatched', False)
#matcher.set_property('MatchingCriteria', 'UseFTDeltaRvalues')
matcher.set_property('MatchingCriteria', 'RecomputeDeltaRvalues')
matcher.set_property('DeltaRcut', 0.5)
matcher.set_property('Debug', True)
matched_jets = matcher.match()
for index, jet in enumerate(matched_jets):
  print(f'Jet {index} is {"" if jet.is_matched() else "not "}matched')
  if jet.is_matched():
    print(f'{jet.get_match_type() = }')
    print(f'{jet.get_match_barcode() = }')
