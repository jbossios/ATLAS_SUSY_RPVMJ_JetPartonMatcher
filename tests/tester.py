def run_tester(matching_criteria = ''):
  import sys
  
  # Logging
  import logging
  logging.basicConfig(level='INFO',format='%(levelname)s: %(message)s')
  log = logging.getLogger()
  
  # Protection
  if not matching_criteria:
    log.error('matching_criteria argument not set, exiting')
    sys.exit(1)
  
  # Import matcher
  import sys
  sys.path.insert(1, '../') # insert at 1, 0 is the script path
  from rpv_matcher.rpv_matcher import RPVJet
  from rpv_matcher.rpv_matcher import RPVParton
  from rpv_matcher.rpv_matcher import RPVMatcher
  
  # Construct jets
  selected_jets = [RPVJet(), RPVJet(), RPVJet(), RPVJet()]
  
  # Leading jet
  selected_jets[0].SetPtEtaPhiE(35, 0, 1.2, 35)
  if matching_criteria == 'UseFTDeltaRvalues':
    selected_jets[0].set_matched_parton_barcode(-1)
  
  # Second-leading jet
  selected_jets[1].SetPtEtaPhiE(25, 0, 0.25, 25)
  if matching_criteria == 'UseFTDeltaRvalues':
    selected_jets[1].set_matched_parton_barcode(2)
  
  # Third-leading jet (matches leading FSR)
  selected_jets[2].SetPtEtaPhiE(21, 0, 3.1, 21)
  if matching_criteria == 'UseFTDeltaRvalues':
    selected_jets[2].set_matched_parton_barcode(-1)
    selected_jets[2].set_matched_fsr_barcode(1)
  
  # Fourth-leading jet (matches second FSR)
  selected_jets[3].SetPtEtaPhiE(20, 0, 3, 20)
  if matching_criteria == 'UseFTDeltaRvalues':
    selected_jets[3].set_matched_parton_barcode(-1)
    selected_jets[3].set_matched_fsr_barcode(2)
  
  # Construct two partons and an FSR, all from same gluino
  
  # Construct partons
  partons = [RPVParton(), RPVParton()]
  partons[0].SetPtEtaPhiE(40, 0, 1, 40) # matches leading jet
  partons[0].set_gluino_barcode(1)
  partons[0].set_barcode(1)
  partons[0].set_pdgid(1)
  
  partons[1].SetPtEtaPhiE(20, 0, 0.2, 20) # matches third leading jet
  partons[1].set_gluino_barcode(1)
  partons[1].set_barcode(2)
  partons[1].set_pdgid(3)
  
  # Construct FSRs
  fsrs = [RPVParton(), RPVParton()]
  fsrs[0].SetPtEtaPhiE(22, 0, 3.2, 22) # matches third-leading jet
  fsrs[0].set_quark_barcode(3)
  fsrs[0].set_gluino_barcode(1)
  fsrs[0].set_barcode(1)
  fsrs[0].set_pdgid(1)
  
  fsrs[1].SetPtEtaPhiE(20, 0, 3, 20) # matches fourth-leading jet
  fsrs[1].set_quark_barcode(3)
  fsrs[1].set_gluino_barcode(1)
  fsrs[1].set_barcode(2)
  fsrs[1].set_pdgid(1)
  
  # Match jets to partons and FSRs
  matcher = RPVMatcher(Jets = selected_jets, Partons = partons, FSRs = fsrs)
  matcher.set_property('ReturnOnlyMatched', False)
  matcher.set_property('MatchingCriteria', matching_criteria)
  if 'RecomputeDeltaRvalues' in matching_criteria:
    matcher.set_property('DeltaRcut', 0.5)
  matcher.set_property('Debug', True)
  matched_jets = matcher.match()
  
  # Write output file
  output_file_name = f'tests/test_{matching_criteria}.new'
  with open(output_file_name, 'w') as ofile:
    for index, jet in enumerate(matched_jets): # loop over matched jets
      ofile.write(f'Jet {index} is {"" if jet.is_matched() else "not "}matched \n')
      if jet.is_matched():
        ofile.write(f'{jet.get_match_type() = }\n')
        ofile.write(f'{jet.get_match_barcode() = }\n')
  
  # Compare with reference
  import filecmp
  result = filecmp.cmp(output_file_name, output_file_name.replace('new', 'ref'), shallow=False)
  if result:
    print(f'Test passed for MatchingCriteria == {matching_criteria}')
  else:
    print(f'Test NOT passed for MatchingCriteria == {matching_criteria} \n')
    print('If changes are expected/understood, update the reference!\n')
    print(f'Content of {output_file_name}:')
    with open(output_file_name, 'r') as ifile:
      print(ifile.read())
    print(f'Content of {output_file_name.replace("new", "ref")}:')
    with open(output_file_name.replace('new', 'ref'), 'r') as ifile:
      print(ifile.read())
    sys.exit(1)

if __name__ == '__main__':
  run_tester('UseFTDeltaRvalues')
  run_tester('RecomputeDeltaRvalues_drPriority')
  run_tester('RecomputeDeltaRvalues_ptPriority')
