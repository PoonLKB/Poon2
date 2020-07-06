import sys
import argparse

from wx import App

from version import __VERSION__
from controlpanel import HondaECU_ControlPanel

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--noredirect', action='store_true', help="don't redirect stdout/stderr to gui")
    parser.add_argument('-V', '--version', action='store_true', help="show version information")
    args = parser.parse_args()

    if args.version:
        print(__VERSION__)
        sys.exit(0)

    app = App(redirect=not args.noredirect, useBestVisual=True)
    gui = HondaECU_ControlPanel(__VERSION__)
    app.MainLoop()
