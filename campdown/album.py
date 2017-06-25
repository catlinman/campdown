
import html

from .helpers import *
from .track import Track

import requests


class Album:
    '''
    Album class of Campdown. Used by the main downloader as well as the
    discography class. This class takes in a URL and treats it as a Bandcamp
    album page. Takes over downloading of files as well as fetching of general
    information which can be used by other modules.

    Args:
        url (str): Bandcamp URL to analyse and download from.
        output (str): relative or absolute path to write to.
        request (request): if supplied this given request's content will be
            analysed instead of making a new request to the mandatory URL.
        verbose (bool): sets if status messages and general information
            should be printed. Errors are still printed regardless of this.
        silent (bool): sets if error messages should be hidden.
        short (bool): omits arist and album fields from downloaded track filenames.
        range_length (number): length of ranged requests in bytes.
        art_enabled (bool): if True the Bandcamp page's artwork will be
            downloaded and saved alongside each of the found tracks.
        id3_enabled (bool): if True tracks downloaded will receive new ID3 tags.
    '''

    def __init__(self, url, output, request=None, verbose=False, silent=False, short=False, range_length=0, art_enabled=True, id3_enabled=True):
        # Requests and other information can optionally be filled to remove unneccessary
        # operations such as making a request to a URL that has already been fetched
        # by another component.

        self.url = url  # URL to download files from.
        self.output = output  # Output directory for downloads.

        # Basic information used when writing tracks.
        self.title = None
        self.artist = None

        # Extra URLs to make further requests easier.
        self.base_url = None
        self.art_url = None

        self.queue = []  # Queue array to store album tracks in.

        # Store the album request object for later reference.
        self.request = request
        self.content = None

        # Set if status messages should be printed to the console.
        self.verbose = verbose

        # Set if error messages should be silenced.
        self.silent = silent

        # Set if the filename should be kept short.
        self.short = short

        # Store the length to be used for ranged requests.
        self.range_length = range_length

        # Set if the cover should be downloaded as well.
        # This is active for albums by default.
        self.art_enabled = art_enabled

        # Set if ID3 tags should be written to the output file.
        self.id3_enabled = id3_enabled

    def prepare(self):
        '''
        Prepares the album class by gathering information about the album and
        it's tracks. If no previous request was made and supplied during
        instantiation one will be made at this point. This process does not
        require making requests to the track URLs.

        Returns:
            True if preparation is successful. False if an error occurred.
        '''

        if not valid_url(self.url):  # Validate the URL
            if not self.silent:
                print("The supplied URL is not a valid URL.")

            return False

        if not self.request:
            # Make a request to the album URL.
            self.request = safe_get(self.url)

        if self.request.status_code != 200:
            if not self.silent:
                print("An error occurred while trying to access your supplied URL. Status code: {}".format(
                    self.request.status_code))

            self.request = None

            return False

        # Get the content from the request and decode it correctly.
        self.content = self.request.content.decode('utf-8')

        # Verify that this is an album page.
        if not page_type(self.content) == "album":
            if not self.silent:
                print("The supplied URL is not an album page.")

            return False

        # Get the meta information for the track.
        meta = html.unescape(string_between(self.content, '<meta name="title" content="', '">')).strip()

        # Get the title of the album.
        if not self.title:
            self.title = meta.split(", by ", 1)[0]

        # Get the main artist of the album.
        # Find the artist title of the supplied Bandcamp page.
        if not self.artist:
            self.artist = meta.split(", by ", 1)[1]

            if self.artist == "Various Artists":
                self.artist = ""

            if not self.artist:
                self.artist = html.unescape(string_between(string_between(
                    self.content, "var BandData = {", "}"), 'name : "', '",'))

            if not self.artist:
                self.artist = html.unescape(string_between(string_between(
                    self.content, "var BandData = {", "}"), 'name: "', '",'))

            if not self.artist:
                if not self.silent:
                    print("\nFailed to prepare the band/artist title")

        # Make the album name safe for file writing.
        self.title = safe_filename(self.title)
        self.artist = safe_filename(self.artist)

        # Setup the correct output directory name.
        self.output = os.path.join(
            self.output, self.artist + " - " + self.title, "")

        # Create a new album folder if it doesn't already exist.
        if not os.path.exists(self.output):
            os.makedirs(self.output)

        # Retrieve the base page URL.
        self.base_url = "{}//{}".format(str(self.url).split("/")[
            0], str(self.url).split("/")[2])

        # prepare the album URL.
        self.art_url = string_between(
            self.content, '<a class="popupImage" href="', '">')

        return True

    def fetch(self):
        '''
        Gathers required information for the tracks in this album and prepares
        them to be used by the download method. Requests are made to each of the
        tracks' Bandcamp pages. Requires the prepare method to be run beforehand.
        '''

        # Split the string and convert it into an array.
        tracks = self.content.split(
            '<table class="track_list track_table" id="track_table">', 1)[1].split('</table>')[0].split("<tr")

        # Iterate over the tracks found and begin traversing the given
        # track's title information and insert the track data in the queue.
        if self.verbose:
            print('\nListing found tracks')

        track_index = 0

        for i, track in enumerate(tracks):
            position = track.find('<a href="/track/')

            if position == -1:
                continue

            # Find the track's name.
            position += 16
            track_name = ""

            while track[position] != '"':
                track_name += track[position]
                position += 1

            if track_name == "":
                continue

            track_index += 1

            # Create a new track instance with the given URL.
            track = Track(self.base_url + "/track/" + track_name, self.output,
                          album=self.title,
                          album_artist=self.artist,
                          index=track_index,
                          verbose=self.verbose,
                          silent=self.silent,
                          short=self.short,
                          range_length=self.range_length
                          )

            # Retrive track data and store it in the instance.
            if track.prepare():
                if self.verbose:
                    safe_print("{}. {}".format(track_index, track.url))

                # Insert the acquired data into the queue.
                self.queue.insert(track_index, track)

            else:
                if self.verbose:
                    safe_print(strike("{}. {}".format(i, track.url)))

    def download(self):
        '''
        Starts the download process for each of the queue's items. This method
        requires the fetch method to be run beforehand.
        '''

        if self.verbose:
            safe_print('\nWriting album to {}'.format(self.output))

        for i in range(0, len(self.queue)):
            self.queue[i].download()

        if self.art_enabled:
            s = download_file(self.art_url, self.output,
                              "cover" + self.art_url[-4:])

            if self.verbose:
                if s == 1:
                    safe_print('\nSaved album art to {}{}{}'.format(
                        self.output, "cover", self.art_url[-4:]))

                elif s == 2:
                    print('\nArtwork already found.')

                else:
                    print('\nFailed to download the artwork. Error code {}'.format(s))
