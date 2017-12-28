"""Module used to isolate the building of the argument parser object"""
import argparse as flag
import logging as l

PARSER = flag.ArgumentParser(
    prog="sapfy",
    description="Spotify sapper"  # TODO Better description
)

PARSER.add_argument('-v', action='store_const',
                    const=l.DEBUG, default=l.INFO)
