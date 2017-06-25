
"""Campdown
Usage:
    campdown <URL>
             [--output=DIR]
             [--range=LENGTH]
             [--quiet]
             [--short]
             [--no-art]
             [--no-id3]
    campdown (-h | --help)
    campdown (-v | --version)

Options:
    -h --help           Show this screen.
    -v --version        Show version.

    -o --output=<DIR>   Output folder to work in.
    -r --range=<LENGTH> Length of ranged requests in bytes.
    -q --quiet          Should output messages be hidden.
    -s --short          Should the output filenames be kept short.
    --no-art            Sets if artwork downloading should be ignored.
    --no-id3            Sets if ID3 tagging should be ignored.

Description:
    Command line Bandcamp downloader. Takes in Bandcamp page URLs and fetches
    tracks, albums as well as their metadata and covers while retaining clean
    and concise formatting of output information.

Requirements:
    Python 3.4+, requests, mutagen, docopt
"""

import sys
import os

from docopt import docopt

from .helpers import *
from .track import Track
from .album import Album
from .discography import Discography

import requests


def cli():
    # Acts as the CLI for the project and main entry point for the command.
    args = docopt(__doc__, version='campdown 1.2')

    try:
        output_dir = args['--output']

    except(IndexError):
        output_dir = ""

    downloader = Downloader(
        args['<URL>'],
        out=output_dir,
        verbose=(not args['--quiet']),
        short=(args['--short']),
        range_length=(int(args['--range']) if args['--range'] else 0),
        art_enabled=(not args['--no-art']),
        id3_enabled=(not args['--no-id3'])
    )

    try:
        downloader.run()

    except (KeyboardInterrupt):
        if not args['--quiet']:
            print("\nInterrupt caught. Exiting program...")

        sys.exit(2)


class Downloader:
    '''
    Main class of Campdown. This class handles all other Campdown functions and
    executes them depending on the information it is given during initilzation.

    Args:
        url (str): Bandcamp URL to analyse and download from.
        out (str): relative or absolute path to write to.
        verbose (bool): sets if status messages and general information
            should be printed. Errors are still printed regardless of this.
        silent (bool): sets if error messages should be hidden.
        short (bool): omits arist and album fields from downloaded track filenames.
        range_length (number): length of ranged requests in bytes.
        art_enabled (bool): if True the Bandcamp page's artwork will be
            downloaded and saved alongside each of the found tracks.
        id3_enabled (bool): if True tracks downloaded will receive new ID3 tags.
    '''

    def __init__(self, url, out=None, verbose=False, silent=False, short=False, range_length=0, id3_enabled=True, art_enabled=True):
        self.url = url
        self.output = out
        self.verbose = verbose
        self.silent = silent
        self.short = short
        self.range_length = range_length
        self.id3_enabled = id3_enabled
        self.art_enabled = art_enabled

        # Variables used during retrieving of information.
        self.request = None
        self.content = None

        # Get the script path in case no output path is specified.
        # self.work_path = os.path.join(
        #     os.path.dirname(os.path.abspath(__file__)), '')

        self.work_path = os.path.join(os.getcwd(), '')

        if self.output:
            # Make sure that the output folder has the right path syntax
            if not os.path.isabs(self.output):
                if not os.path.exists(os.path.join(self.work_path, self.output)):
                    os.makedirs(os.path.join(self.work_path, self.output))

                self.output = os.path.join(self.work_path, self.output)

        else:
            # If no path is specified use the absolute path of the main file.
            self.output = self.work_path

    def run(self):
        '''
        Begins downloading the content from the prepared settings.
        '''

        if not valid_url(self.url):
            if not self.silent:
                print("The supplied URL is not a valid URL.")

            return False

        # Get the content from the supplied Bandcamp URL.
        self.request = safe_get(self.url)
        self.content = self.request.content.decode('utf-8')

        if self.request.status_code != 200:
            if not self.silent:
                print("An error occurred while trying to access your supplied URL. Status code: {}".format(
                    self.request.status_code))

            return

        # Get the type of the page supplied to the downloader.
        pagetype = page_type(self.content)

        if pagetype == "track":
            if self.verbose:
                print("\nDetected Bandcamp track.")

            track = Track(
                self.url,
                self.output,
                request=self.request,
                verbose=self.verbose,
                silent=self.silent,
                short=self.short,
                range_length=self.range_length,
                art_enabled=self.art_enabled,
                id3_enabled=self.id3_enabled
            )

            if track.prepare():  # Prepare the track by filling out content.
                track.download()  # Begin the download process.

                if self.verbose:
                    print("\nFinished track download. Downloader complete.")

            else:
                if self.verbose:
                    print(
                        "\nThe track you are trying to download is not publicly available. Consider purchasing it if you want it.")

        elif pagetype == "album":
            if self.verbose:
                print("\nDetected Bandcamp album.")

            album = Album(
                self.url,
                self.output,
                request=self.request,
                verbose=self.verbose,
                silent=self.silent,
                short=self.short,
                range_length=self.range_length,
                art_enabled=self.art_enabled,
                id3_enabled=self.id3_enabled
            )

            if album.prepare():  # Prepare the album with information from the supplied URL.
                album.fetch()  # Make the album prepare it's tracks.
                album.download()  # Start the download process.

            if self.verbose:
                print("\nFinished album download. Downloader complete.")

        elif pagetype == "discography":
            if self.verbose:
                print("\nDetected Bandcamp discography page.")

            page = Discography(
                self.url,
                self.output,
                request=self.request,
                verbose=self.verbose,
                silent=self.silent,
                short=self.short,
                range_length=self.range_length,
                art_enabled=self.art_enabled,
                id3_enabled=self.id3_enabled
            )

            page.prepare()  # Make discography gather all information it requires.
            page.fetch_download()  # Begin the download process.

            if self.verbose:
                print("\nFinished discography download. Downloader complete.")

        else:
            if not self.silent:
                print("Invalid page type. Exiting.")
