import sys

from orukural import brewlibs


def pytest_configure(config):
    # re-running pytest with Homebrew's libraries on the path: hand the real terminal back first, or the
    # new run's output is lost in this one's capture
    capman = config.pluginmanager.getplugin("capturemanager")
    if capman and brewlibs.needed():
        capman.suspend_global_capture(in_=True)
    brewlibs.ensure(["-m", "pytest"] + sys.argv[1:])
