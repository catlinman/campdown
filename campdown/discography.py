
import html

from .helpers import *
from .track import Track
from .album import Album


class Discography:

    """
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
        sleep (number): timeout duration between failed requests in seconds.
        art_enabled (bool): if True the Bandcamp page's artwork will be
            downloaded and saved alongside each of the found albums/tracks.
        id3_enabled (bool): if True tracks downloaded will receive new ID3 tags.
    """

    def __init__(self, url, output, request=None, verbose=False, silent=False, short=False, sleep=30, art_enabled=True, id3_enabled=True, abort_missing=False):
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

        # Store the timeout duration between failed requests.
        self.sleep = sleep

        # Set if the cover should be downloaded as well.
        self.art_enabled = art_enabled

        # Set if ID3 tags should be written to files.
        self.id3_enabled = id3_enabled

        # Sets if a missing album track aborts the entire album download.
        self.abort_missing = abort_missing

    def prepare(self):
        """
        Prepares the discography class by gathering information about albums and
        tracks. If no previous request was made and supplied during instantiation
        one will be made at this point. This process does not require making
        requests to the album and track URLs.
        """

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

        print(self.base_url)

        meta = html.unescape(string_between(self.content, '<meta name="Description" content="', ">")).strip()
        self.artist = meta.split(".\n", 1)[0]

        if self.artist:
            self.output = os.path.join(self.output, self.artist, "")

            # Create a new artist folder if it doesn't already exist.
            if not os.path.exists(self.output):
                os.makedirs(self.output)

            safe_print(
                '\nSet "{}" as the working directory.'.format(self.output))

        # Make the artist name safe for file writing.
        self.artist = safe_filename(self.artist)

        # Define search markers to find the index of for track URLs.
        track_search_markers = [
            '<a href="/track/',
            '<a href="{}/track/'.format(self.base_url),
            '<a href="https://\w+.bandcamp.com/track/'
        ]

        # Run a search through our track markers and handle regex options and duplicates.
        track_filtered_markers = []
        for marker in track_search_markers:
            results = re.findall(marker, self.content)

            for result in results:
                if result not in track_filtered_markers:
                    track_filtered_markers.append(result)

        # Create a list of indices for track links.
        tracks = []
        for marker in track_filtered_markers:
            tracks.extend(find_string_indices(self.content, marker))

        # Define search markers to find the index of for album URLs.
        album_search_markers = [
            '<a href="/album/',
            '<a href="{}/album/'.format(self.base_url),
            '<a href="https://\w+.bandcamp.com/album/'
        ]

        # Run a search through our album markers and handle regex options and duplicates.
        album_filtered_markers = []
        for marker in album_search_markers:
            results = re.findall(marker, self.content)

            for result in results:
                if result not in album_filtered_markers:
                    album_filtered_markers.append(result)

        # Create a list of indices for album links.
        albums = []
        for marker in album_filtered_markers:
            albums.extend(find_string_indices(self.content, marker))

        if self.verbose:
            print('\nListing found discography content')

        for i, position in enumerate(albums):
            album_url = ""

            # Begin iteration over characters until the string begins.
            while self.content[position] != '"':
                position += 1

            # Begin iteration over characters until the string closes.
            while self.content[position + 1] != '"' and self.content[position + 1] != '?':
                album_url += self.content[position + 1]
                position += 1

            if album_url == "":
                continue

            if "http://" not in album_url and "https://" not in album_url:
                album_url = self.base_url + album_url

            # Print the prepared track.
            if self.verbose:
                safe_print(album_url)

            # Create a new track instance with the given URL.
            album = Album(
                album_url,
                self.output,
                verbose=self.verbose,
                silent=self.silent,
                short=self.short,
                sleep=self.sleep,
                art_enabled=self.art_enabled,
                id3_enabled=self.id3_enabled,
                abort_missing=self.abort_missing
            )

            self.queue.insert(len(self.queue), album)

        for i, position in enumerate(tracks):
            track_url = ""

            # Begin iteration over characters until the string begins.
            while self.content[position] != '"':
                position += 1

            # Begin iteration over characters until the string closes.
            while self.content[position + 1] != '"' and self.content[position + 1] != '?':
                track_url += self.content[position + 1]
                position += 1

            if track_url == "":
                continue

            if not "http://" in track_url and not "https://" in track_url:
                track_url = self.base_url + track_url

            # Print the prepared track.
            if self.verbose:
                safe_print(track_url)

            # Create a new track instance with the given URL.
            track = Track(
                track_url,
                self.output,
                verbose=self.verbose,
                art_enabled=self.art_enabled,
                id3_enabled=self.id3_enabled
            )

            self.queue.insert(len(self.queue), track)

        if self.verbose:
            print("\nBeginning downloads. Albums additionally require fetching tracks.")

        return True

    def fetch(self):
        """
        Tells eachs of the queue's items to fetch their individual information
        from their respective Bandcamp pages. This means that requests are made
        to these pages. Requires the queue to be created by the prepare method
        beforehand.
        """

        for i in range(0, len(self.queue)):
            if type(self.queue[i]) is Track:
                # If we received a metadata return, delete the track data.
                if not self.queue[i].prepare():
                    self.queue[i] = None

            elif type(self.queue[i]) is Album:
                if self.queue[i].prepare():
                    # If we received a bad fetch, delete the album data.
                    if not self.queue[i].fetch():
                        self.queue[i] = None

    def download(self):
        """
        Starts the download process for each of the queue's items. This method
        requires the fetch method to be run beforehand.
        """

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
