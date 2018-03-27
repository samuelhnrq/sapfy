'''Module used to isolate the building of the argument parser object'''
import argparse as flag
import logging as l
import soundfile as sf

PARSER = flag.ArgumentParser(
    prog='sapfy',
    description="Spotify daemon intended to sap spotify's songs as they play.")

PARSER.add_argument(
    '-v',
    action='store_const',
    help='Enables verbose output',
    const=l.DEBUG,
    default=l.INFO)
PARSER.add_argument(
    '-f',
    '--format',
    default='FLAC',
    metavar='<audio file extension>',
    help='Audio format of the output file',
    choices=sf.available_formats().keys())
PARSER.add_argument(
    '-o',
    '--output',
    default='{albumArtist[0]}/{album}/{trackNumber} {title}',
    help='A string with formatting placeholders like artist and title and etc. '
    'See documentation for more information. The path is relative to the '
    'target folder.')
PARSER.add_argument(
    '-t',
    '--target',
    default='./',
    help='The target folder where the musics go')
PARSER.add_argument(
    '-s',
    '--strict-length',
    nargs='?',
    type=int,
    dest='strict_length',
    default=1500,
    const=10,
    metavar='x',
    help='If this is set it will delete all the songs that are more than X '
    'seconds different from the actual (metadata) song length.')
PARSER.add_argument(
    '-a',
    '--ads-only',
    dest='ads_only',
    action='store_true',
    help='Disable song recording and only act as a ad-skipping daemon')
OPTIONS = PARSER.parse_args()
