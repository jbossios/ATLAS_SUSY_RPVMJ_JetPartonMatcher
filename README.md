
# <div align='center'>JetParton matcher for ATLAS SUSY RPV Multijet analysis</div>

## Dependencies

- Python3.8+
- External python modules: ROOT

## How does it work?

The ```RPVMatcher``` class matches jets to last quark in the gluino decay chain (and optionally FSRs).

### Inputs:

Three types of inputs are supported:

- Jets: jets are provided as a list of ```RPVJet``` objects
- Last quarks in gluino decay chain are provided as a list of ```RPVParton``` objects
- FSRs are provided as a list of ```RPVParton``` objects

Inputs can be provided during initialization:

```
matcher = RPVMatcher(Jets = selected_jets, Partons = partons, [FSRs = fsrs])
```

or can be added using the appropriate methods:

```
add_jets(self, jets: [RPVJet])
add_partons(self, partons: [RPVParton])
add_fsrs(self, fsrs: [RPVParton])
```

### Properties:

The following properties can be set through the ```set_property()``` method:

- 'ReturnOnlyMatched' (value type: ```bool```): set to ```True``` to return only matched jets (```False``` by default)
- 'MatchingCriteria' (value type: ```str```): there are currently two options: 'UseFTDeltaRvalues' and 'RecomputeDeltaRvalues'
- 'DeltaRcut' (value type: ```float```): maximum DeltaR value cut used for matching jets to partons (only used when ```'MatchingCriteria' == 'RecomputeDeltaRvalues'```)
- 'Debug' (value type: ```bool```): enable debugging (higher verbosity)

### How to prepare jets?

A ```list``` of ```RPVJet``` objects must be created. Each jet (instance of ```RPVJet```) must call ```SetPtEtaPhiE()``` to set thet jet's kinematics.

In addition, if ```"MatchingCriteria"``` is set to ```"UseFTDeltaRvalues"``` the corresponding methods need to be called (```set_matched_parton_barcode()``` for partons and ```set_matched_fsr_barcode()``` for FSRs).

### How to prepare partons (last quark in the gluino decay chain)?

A ```list``` of ```RPVParton``` objects must be created. Each parton (instance of ```RPVParton```) must call ```SetPtEtaPhiE()``` to set the parton's kinematics.

In addition, if ```"MatchingCriteria"``` is set to ```"UseFTDeltaRvalues"``` the following methods need to be called:

```
set_gluino_barcode()
set_barcode()
set_pdgid()
```

### How to prepare FSRs?

A ```list``` of ```RPVParton``` objects must be created. Each FSR (instance of ```RPVParton```) must call ```SetPtEtaPhiE()``` to set the FSR's kinematics.

In addition, if ```"MatchingCriteria"``` is set to ```"UseFTDeltaRvalues"``` the following methods need to be called:

```
set_quark_barcode() # barcode of corresponding parton from the same gluino decay chain
set_gluino_barcode()
set_barcode()
set_pdgid()
```

### How to run?

Run the ```match()``` method of ```RPVMatcher``` which will retrieve decorated jets with all the relevant information.

The following methods can be called after jets are matched:

```
is_matched()
get_match_type() # will return "Parton" or "FSR" if matched and "None" if not
get_match_barcode()
get_match_parton_index()
get_match_pdgid()
get_match_barcode()
get_match_gluino_barcode()

```

## Example

An example can be found in the repository as example.py
