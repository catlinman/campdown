
import html
import json

from .helpers import *

import requests
from mutagen.id3 import ID3NoHeaderError
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, TDRC, TRCK


class Track:
    '''
    Track class of Campdown. Base class of Campdown. Takes care of downloading of
    information and streaming of file contents. This file directly uses the
    download_file function to get the mp3 file from the supplied URLs data.
    The track class is used by every other class of Campdown and partially
    receives information from this related classes.

    Args:
        url (str): Bandcamp URL to analyse and download from.
        output (str): relative or absolute path to write to.
        request (request): if supplied this given request's content will be
            analysed instead of making a new request to the mandatory URL.
        album (str): optionally the album this track belongs to.
        album_artist (str): album artist index
        index (str): optionally the index this track has in the album.
        verbose (bool): sets if status messages and general information
            should be printed. Errors are still printed regardless of this.
        silent (bool): sets if error messages should be hidden.
        short (bool): omits arist and album fields from downloaded track filenames.
        range_length (number): length of ranged requests in bytes.
        art_enabled (bool): if True the Bandcamp page's artwork will be
            downloaded and saved alongside each of the found tracks.
        id3_enabled (bool): if True tracks downloaded will receive new ID3 tags.
    '''

    def __init__(self, url, output, request=None, album=None, album_artist=None, index=None, verbose=False, silent=False, short=False, range_length=0, art_enabled=False, id3_enabled=True):
        # Requests and other information can optionally be filled to remove unneccessary
        # operations such as making a request to a URL that has already been fetched
        # by another component.

        self.url = url  # URL to download files from.
        self.output = output  # Output directory for the track download.

        # Information about the given track. These are assigned in the prepare
        # function which needs to be called before anything else can be done.
        self.title = None
        self.artist = None
        self.date = None

        # These values should be set by passing arguments to the constructor.
        # Album is used to set a fixed album name and to keep name consistency.
        # Index is used to number the track in the filename.
        self.album = album
        self.album_artist = album_artist
        self.index = index

        # Information about the track fetched from Bandcamp in JSON format.
        self.info = None

        self.art_url = None
        self.mp3_url = None

        # Store the track request object for later reference.
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
        # This is disabled for tracks by default.
        self.art_enabled = art_enabled

        self.id3_enabled = id3_enabled

    def prepare(self):
        '''
        Prepares the track by gathering information. If no previous request was
        made and supplied during instantiation one will be made at this point.

        Returns:
            True if preparation is successful. False if an error occurred.
        '''

        if not valid_url(self.url):  # Validate the URL
            print("The supplied URL is not a valid URL.")
            return False

        if not self.request:
            # Make a request to the track URL.
            self.request = safe_get(self.url)

        if self.request.status_code != 200:
            print("An error occurred while trying to access your supplied URL. Status code: {}".format(
                self.request.status_code))

            self.request = None

            return False

        # Get the content from the request and decode it correctly.
        self.content = self.request.content.decode('utf-8')

        # Verify that this is a track page.
        if not page_type(self.content) == "track":
            if not self.silent:
                print("The supplied URL is not a track page.")

        # Get the metadata for the track.
        meta = html.unescape(string_between(self.content, '<meta name="title" content="', '">')).strip()

        # Get the title of the track.
        if not self.title:
            self.title = meta.split(", by ", 1)[0]

        # Get the main artist of the track.
        if not self.artist:
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
                print("\nFailed to prepare the band/artist title")

        # Add the album to which this single track might belong to.
        if not self.album:
            try:
                self.album = html.unescape(string_between(
                    self.content, '<span itemprop="name">', "</span>"))

            except IndexError:
                self.album = ""

        # prepare the date this track was released on.
        if not self.date:
            try:
                self.date = html.unescape(string_between(
                    self.content, '<meta itemprop="datePublished" content="', '">'))[0:4]

            except IndexError:
                self.date = ""

        # Make the track name safe for file writing.
        self.title = safe_filename(self.title)
        self.artist = safe_filename(self.artist)
        self.album = safe_filename(self.album)

        # prepare the track art URL.
        self.art_url = string_between(
            self.content, '<a class="popupImage" href="', '">')

        # Get the Bandcamp track MP3 URL and save it.
        raw_info = "{" + string_between(
            self.content, "trackinfo: [{", "}]") + "}"

        info = json.loads(raw_info)

        if info["file"]:
            self.mp3_url = info["file"]["mp3-128"]

            try:
                # Add in http for those times when Bandcamp is rude.
                if self.mp3_url[:2] == "//":
                    self.mp3_url = "http:" + self.mp3_url

            except TypeError:
                return False

            return True

        else:
            return False

    def download(self):
        '''
        Starts the download process for this track. Also writes the file and
        applies ID3 tags if specified. Requires the track to have been prepared
        by the prepare method beforehand.
        '''

        if not self.album:
            safe_print('\nWriting file to {}'.format(self.output))

        # Clean up the main title.
        if not self.short:
            clean_title = format_information(
                self.title,
                self.artist,
                self.album,
                self.index
            )

        else:
            clean_title = short_information(
                self.title,
                self.index
            )

        # Download the file.
        s = download_file(
            self.mp3_url,
            self.output,
            clean_title + ".mp3",
            verbose=self.verbose,
            silent=self.silent,
            range_length=self.range_length
        )

        if s > 2 and not self.silent:
            print('\nFailed to download the file. Error code {}'.format(s))

            return s

        # Write ID3 tags if the id3_enabled is true.
        if self.id3_enabled:
            # Fix ID3 tags. Create ID3 tags if not present.
            try:
                tags = ID3(os.path.join(self.output, safe_filename(clean_title + ".mp3")))

            except ID3NoHeaderError:
                tags = ID3()

            # Title and artist tags. Split the title if it contains the artist tag.
            if " - " in self.title:
                split_title = str(self.title).split(" - ", 1)

                tags["TPE1"] = TPE1(encoding=3, text=str(split_title[0]))
                tags["TIT2"] = TIT2(encoding=3, text=str(split_title[1]))

            else:
                tags["TIT2"] = TIT2(encoding=3, text=str(self.title))

                tags["TPE1"] = TPE1(encoding=3, text=str(self.artist))

            # Album tag. Make sure we have it.
            if self.album:
                tags["TALB"] = TALB(encoding=3, text=str(self.album))

            # Track index tag.
            if self.index:
                tags["TRCK"] = TRCK(encoding=3, text=str(self.index))

            # Track date.
            if self.date:
                tags["TDRC"] = TDRC(encoding=3, text=str(self.date))

            # Album artist
            if not self.album_artist:
                self.album_artist = self.artist

            tags["TPE2"] = TPE2(encoding=3, text=str(self.album_artist))

            # Retrieve the base page URL.
            base_url = "{}//{}".format(str(self.url).split("/")[
                0], str(self.url).split("/")[2])

            # Add the Bandcamp base comment in the ID3 comment tag.
            tags["COMM"] = COMM(encoding=3, lang='XXX', desc=u'', text=u'Visit {}'.format(base_url))

            # Save all tags to the track.
            tags.save(os.path.join(self.output, safe_filename(clean_title + ".mp3")))

        # Download artwork if it is enabled.
        if self.art_enabled:
            s = download_file(self.art_url, self.output,
                              clean_title + self.art_url[-4:])

            if s == 1:
                if self.verbose:
                    safe_print('\nSaved track art to {}{}{}'.format(
                        self.output, clean_title, self.art_url[-4:]))

            elif s == 2:
                if self.verbose:
                    print('\nArtwork already found.')

            elif not self.silent:
                print('\nFailed to download the artwork. Error code {}'.format(s))
