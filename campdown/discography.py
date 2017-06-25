
import html

from .helpers import *
from .track import Track
from .album import Album


class Discography:
    '''
    Discography class of Campdown. This class takes in a URL and treats it as a
    Bandcamp discography page. Takes over downloading of files as well as
    fetching of general information which can be used by other modules

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
            downloaded and saved alongside each of the found albums/tracks.
        id3_enabled (bool): if True tracks downloaded will receive new ID3 tags.
    '''

    def __init__(self, url, output, request=None, verbose=False, silent=False, short=False, range_length=0, art_enabled=True, id3_enabled=True):
        # Requests and other information can optionally be filled to remove unneccessary
        # operations such as making a request to a URL that has already been fetched
        # by another component.

        self.url = url  # URL to get information from.
        self.output = output

        # Basic information used when writing tracks.
        self.artist = None

        # Queue array to store album tracks in.
        self.queue = []

        # Store the album request object for later reference.
        self.request = request
        self.content = None

        # Base Bandcamp URL.
        self.base_url = None

        # Set if status messages should be printed to the console.
        self.verbose = verbose

        # Set if error messages should be silenced.
        self.silent = silent

        # Set if the filename should be kept short.
        self.short = short

        # Store the length to be used for ranged requests.
        self.range_length = range_length

        # Set if the cover should be downloaded as well.
        self.art_enabled = art_enabled

        # Set if ID3 tags should be written to files.
        self.id3_enabled = id3_enabled

    def prepare(self):
        '''
        Prepares the discography class by gathering information about albums and
        tracks. If no previous request was made and supplied during instantiation
        one will be made at this point. This process does not require making
        requests to the album and track URLs.
        '''

        if not valid_url(self.url):  # Validate the URL
            print("The supplied URL is not a valid URL.")
            return False

        if not self.request:
            # Make a request to the album URL.
            self.request = safe_get(self.url)

        if self.request.status_code != 200:
            print("An error occurred while trying to access your supplied URL. Status code: {}".format(
                self.request.status_code))

            self.request = None

            return False

        # Get the content from the request and decode it correctly.
        self.content = self.request.content.decode('utf-8')

        # Verify that this is an discography page.
        if not page_type(self.content) == "discography":
            print("The supplied URL is not a discography page.")

        # Retrieve the base page URL.
        self.base_url = "{}//{}".format(str(self.url).split("/")[
            0], str(self.url).split("/")[2])

        meta = html.unescape(string_between(self.content, '<meta name="Description" content="', ">")).strip()
        self.artist = meta.split("\n", 1)[0]

        if self.artist:
            self.output = os.path.join(self.output, self.artist, "")

            # Create a new artist folder if it doesn't already exist.
            if not os.path.exists(self.output):
                os.makedirs(self.output)

            safe_print(
                '\nSet "{}" as the working directory.'.format(self.output))

        # Make the artist name safe for file writing.
        self.artist = safe_filename(self.artist)

        tracks = [i for i in range(
            len(self.content)) if self.content.startswith('<a href="/track/', i)]

        albums = [i for i in range(
            len(self.content)) if self.content.startswith('<a href="/album/', i)]

        if self.verbose:
            print('\nListing found discography content')

        for i, position in enumerate(albums):
            position += 16  # Add the length of the search string.

            album_name = ""

            while self.content[position] != '"':
                album_name += self.content[position]
                position += 1

            if album_name == "":
                continue

            # Print the prepared track.
            if self.verbose:
                safe_print(self.base_url + "/album/" + album_name)

            # Create a new track instance with the given URL.
            album = Album(self.base_url + "/album/" +
                          album_name,
                          self.output,
                          verbose=self.verbose,
                          silent=self.silent,
                          short=self.short,
                          range_length=self.range_length
                          )

            self.queue.insert(len(self.queue), album)

        for i, position in enumerate(tracks):
            position += 16  # Add the length of the search string.

            track_name = ""

            while self.content[position] != '"':
                track_name += self.content[position]
                position += 1

            if track_name != "":
                # Print the prepared track.
                if self.verbose:
                    safe_print(self.base_url + "/track/" + track_name)

                # Create a new track instance with the given URL.
                track = Track(self.base_url + "/track/" +
                              track_name, self.output, verbose=self.verbose, art_enabled=True)

                self.queue.insert(len(self.queue), track)

        if self.verbose:
            print('\nBeginning downloads. Albums additionally require fetching tracks.')

        return True

    def fetch(self):
        '''
        Tells eachs of the queue's items to fetch their individual information
        from their respective Bandcamp pages. This means that requests are made
        to these pages. Requires the queue to be created by the prepare method
        beforehand.
        '''

        for i in range(0, len(self.queue)):
            if type(self.queue[i]) is Track:
                self.queue[i].prepare()

            elif type(self.queue[i]) is Album:
                self.queue[i].prepare()
                self.queue[i].fetch()

    def download(self):
        '''
        Starts the download process for each of the queue's items. This method
        requires the fetch method to be run beforehand.
        '''

        for i in range(0, len(self.queue)):
            if type(self.queue[i]) is Track:
                if self.verbose:
                    safe_print(
                        '\nDownloading track "{}"'.format(self.queue[i].title))

                self.queue[i].download()

            elif type(self.queue[i]) is Album:
                if self.verbose:
                    safe_print(
                        '\nDownloading album "{}"'.format(self.queue[i].title))

                self.queue[i].download()

    def fetch_download(self):
        '''
        Starts the download process for each of the queue's items. This method
        is the same as the download and fetch method but chains them together
        to start download files right away instead of preparing them. Good for
        pages with a lot of tracks and albums.
        '''

        for i in range(0, len(self.queue)):
            if type(self.queue[i]) is Track:
                self.queue[i].prepare()

                if self.verbose:
                    safe_print(
                        '\nDownloading track "{}"'.format(self.queue[i].title))

                self.queue[i].download()

            elif type(self.queue[i]) is Album:
                self.queue[i].prepare()

                if self.verbose:
                    safe_print(
                        '\nDownloading album "{}"'.format(self.queue[i].title))

                self.queue[i].fetch()
                self.queue[i].download()
