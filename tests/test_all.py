from tester import run_tester


def test_RecomputeDeltaRvalues_drPriority():
    run_tester('RecomputeDeltaRvalues_drPriority')


def test_RecomputeDeltaRvalues_ptPriority():
    run_tester('RecomputeDeltaRvalues_ptPriority')


def test_UseFTDeltaRvalues():
    run_tester('UseFTDeltaRvalues')


if __name__ == '__main__':
    test_RecomputeDeltaRvalues_drPriority()
    test_RecomputeDeltaRvalues_ptPriority()
    test_UseFTDeltaRvalues()
