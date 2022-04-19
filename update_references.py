import os

# Schedule pytest
commands = [
    'python3 -m pytest',
]

# Reference files to update
refs = [
    'tests/test_RecomputeDeltaRvalues_drPriority.ref',
    'tests/test_RecomputeDeltaRvalues_ptPriority.ref',
    'tests/test_UseFTDeltaRvalues.ref'
]

# Schedule the update of the reference files 
commands += [f'mv {name.replace("ref", "new")} {name}' for name in refs]

# Execute all commands
command = ' && '.join(commands) + ' && echo ">>> All DONE <<<" &'
os.system(command)
