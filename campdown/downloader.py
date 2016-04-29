
import os

from campdown.helpers import *
from campdown.track import Track
from campdown.album import Album
from campdown.discography import Discography

import requests


class Downloader:
    '''
    Main class of Campdown. This class handles all other Campdown functions and
    executes them depending on the information it is given during initilzation.

    Args:
        url (str): Bandcamp URL to analyse and download from.
        out (str): relative or absolute path to write to.
    '''

    def __init__(self, url, out=None):
        self.url = url
        self.output = out

        # Downloader relevant data.
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
            print("The supplied URL is not a valid URL.")
            return False

        # Get the content from the supplied Bandcamp URL.
        self.request = requests.get(self.url)
        self.content = self.request.content.decode('utf-8')

        if self.request.status_code != 200:
            print("An error occurred while trying to access your supplied URL. Status code: {}".format(
                self.request.status_code))

            return

        # Get the type of the page supplied to the downloader.
        pagetype = page_type(self.content)

        if pagetype == "track":
            print("\nDetected Bandcamp track.")

            track = Track(self.url, self.output,
                          request=self.request, verbose=True, art_enabled=True)

            if track.prepare():  # Prepare the track by filling out content.
                track.download()  # Begin the download process.

                print("\nFinished track download. Downloader complete.")

            else:
                print(
                    "\nThe track you are trying to download is not publicly available. Consider purchasing it if you want it.")

        elif pagetype == "album":
            print("\nDetected Bandcamp album.")

            album = Album(self.url, self.output,
                          request=self.request, verbose=True, art_enabled=True)

            if album.prepare():  # Prepare the album with information from the supplied URL.
                album.fetch()  # Make the album prepare it's tracks.
                album.download()  # Start the download process.

            print("\nFinished album download. Downloader complete.")

        elif pagetype == "discography":
            print("\nDetected Bandcamp discography page.")

            page = Discography(
                self.url, self.output, request=self.request, verbose=True, art_enabled=True)

            page.prepare()  # Make discography gather all information it requires.
            page.fetch_download()  # Begin the download process.

            print("\nFinished discography download. Downloader complete.")

        else:
            print("Invalid page type. Exiting.")
