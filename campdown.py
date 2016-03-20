#!/usr/bin/env python

import os
import sys
import math
import re
import json
import html
import platform  # TODO: Add platform detection to path validation.

import requests


def safe_print(string):
    '''
    Print to the console while avoiding encoding errors

    Args:
        string (str): string to print to the console without encoding errors.
    '''

    try:
        print(string)

    except UnicodeEncodeError:
        try:
            print(string.encode(
                sys.stdout.encoding, errors="replace").decode())

        except UnicodeDecodeError:
            print(string.encode(
                sys.stdout.encoding, errors="replace"))


def safe_path(string):
    '''
    Convert a path string into one without illegal characters

    Args:
        string (str): the path to remove illegal characters from.

    Returns:
        new path string without illegal characters.
    '''
    # TODO Add platform detection as previously mentioned.
    return string.replace('/', '&').replace('\\', '').replace('"', '')


def string_between(string, start, end):
    '''
    Returns a new string between the start and end range.

    Args:
        string (str): the string to split.
        start (str): string to start the split at.
        end (str): string to stop the split at.

    Returns:
        new string between start and end.
    '''
    return str(string).split(str(start), 1)[1].split(str(end))[0]


def format_information(title, artist, album="", index=0):
    '''
    Takes in track information and returns everything as a formatted String.

    Args:
        title (str): track title string
        artist (str): track artist string
        album (str): optional track album string
        index (str): optional track number string

    Returns:
        A formatted string of all track information.
    '''

    if " - " in title:
        split_title = str(title).split(" - ", 1)

        if album:
            if index:
                return "{} - {} - {} {}".format(split_title[0], album, index, split_title[1])

            else:
                return "{} - {} - {}".format(split_title[0], album, split_title[1])

        else:
            if index:
                return "{} - {} {}".format(split_title[0], index, split_title[1])

            else:
                return "{} - {}".format(split_title[0], split_title[1])
    else:
        if album:
            if index:
                return "{} - {} - {} {}".format(artist, album, index, title)

            else:
                return "{} - {} - {}".format(artist, album, title)

        else:
            if index:
                return "{} - {} {}".format(artist, index, title)

            else:
                return "{} - {}".format(artist, title)


def valid_url(url):
    # TODO: Further URL validation.
    if "http://" not in url and "https://" not in url:
        return False

    return True


def page_type(content):
    # Identify a Bandcamp page and it's type by analysing request content.
    # Check if the content contains a track list.
    if "bandcamp.com" in content:
        if "Digital Album" and "track_list" in content:
            return "album"

        elif 'id="discography"' not in content:
            return "discography"

        else:
            return "track"

    else:
        return "none"


def download_file(url, output, name, force=False, verbose=False, silent=False):
    '''
    Downloads and saves a file from the supplied URL and prints progress
    to the console. Uses ranged requests to make downloads from Bandcamp faster.
    Returns 0 if the download failed, 1 if the download was successfull and 2 if
    the download file was already found and has the same file size.

    Args:
        url (str): URL to make the request to.
        output (str): absolute folder path to write to.
        name (str): filename with extension to write the content to.
        force (bool): ignores checking if the file already exists.
        verbose (bool): prints status messages as well as download progress.
        silent (bool): if error messages should be ignored and not printed.

    Returns:
        0 if there was an error in this function
        1 if the download and write is successfull
        2 if the file already exists
        r.status_code if a connection error occurred
    '''

    if verbose:
        safe_print('\nDownloading: {}'.format(name))

    # Get the size of the remote file through a streamed request.
    r = requests.get(url, stream=True)

    if r.status_code != 200:
        if not silent:
            print("Request error {}".format(r.status_code))

        return r.status_code

    total_length = r.headers.get('content-length')

    if total_length is None:
        if not silent:
            print("Request does not contain an entry for the content length.")

        return 0

    if not force:
        if os.path.isfile(os.path.join(output, name)):
            if os.path.getsize(os.path.join(output, name)) != int(total_length):
                if verbose:
                    print(
                        'File already found but the file size doesn\'t match up. Redownloading.')

            else:
                if verbose:
                    print('File already found. Skipping download.')

                return 2

    # Open a file stream which will be used to save the output string
    with open(output + "/" + re.sub('[\\/:*?<>|]', "", name), "wb") as f:
        # Storage variables used while evaluating the already downloaded data.
        dl = 0
        total_length = int(total_length)
        cleaned_length = int((total_length * 100) / pow(1024, 2)) / 100
        block_size = 2048

        for i in range(math.ceil(total_length / 1048576)):
            response = requests.get(url, headers={
                'Range': 'bytes=' + str(i * 1048576) + "-" + str((i + 1) * (1048576) - 1)}, stream=True)

            for chunk in response.iter_content(chunk_size=block_size):
                # Add the length of the chunk to the download size and
                # write the chunk to the file.
                dl += len(chunk)
                f.write(chunk)

                if verbose:
                    # Display a bar based on the current download progress.
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s%s] %sMB / %sMB " % ('=' * done, ">", ' ' * (
                        50 - done), (int(((dl) * 100) / pow(1024, 2)) / 100), cleaned_length))
                    sys.stdout.flush()

    return 1


class Track:

    def __init__(self, url, output, request=None, title=None, artist=None, album=None, index=None, verbose=False, silent=False, art_enabled=False):
        # Requests and other information can optionally be filled to remove unneccessary
        # operations such as making a request to a URL that has already been fetched
        # by another component.

        self.url = url  # URL to download files from.

        # Output directory to create the new album dir in.
        self.output = output

        # Information about the given track. These are assigned in the prepare
        # function which needs to be called before anything else can be done.
        self.title = title
        self.artist = artist
        self.album = album
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

        # Set if the cover should be downloaded as well.
        self.art_enabled = art_enabled

    def fetch(self):
        if not valid_url(self.url):  # Validate the URL
            print("The supplied URL is not a valid URL.")
            return False

        if not self.request:
            # Make a request to the track URL.
            self.request = requests.get(self.url)

        if self.request.status_code != 200:
            print("An error occurred while trying to access your supplied URL. Status code: {}".format(
                self.request.status_code))

            self.request = None

            return False

        # Get the content from the request and decode it correctly.
        self.content = self.request.content.decode('utf-8')

        # Verify that this is a track page.
        if not page_type(self.content) == "track":
            print("The supplied URL is not a track page.")

        # Get the title of the album.
        if not self.title:
            self.title = html.unescape(re.sub(
                '[:*?<>|]', '', string_between(self.content, '<meta name="Description" content=', " by ")[2:]))

        # Get the main artist of the album.
        if not self.artist:
            try:
                self.artist = html.unescape(string_between(
                    string_between(self.content, "var BandData = {", "}"), 'name : "', '",'))

            except IndexError:
                try:
                    self.artist = html.unescape(string_between(
                        string_between(self.content, "var BandData = {", "}"), 'name: "', '",'))

                except:
                    print("\nFailed to fetch the band/artist title")

        # Add the title of the album this single track might belong to, to
        # the information that will make up the output filename.
        if not self.album:
            try:
                self.album = html.unescape(string_between(
                    self.content, '<span itemprop="name">', "</span>"))

            except IndexError:
                self.album = ""

        # Fetch the track art URL.
        self.art_url = string_between(
            self.content, '<a class="popupImage" href="', '">')

        # Get the Bandcamp track MP3 URL and save it.
        raw_info = "{" + string_between(
            self.content, "trackinfo: [{", "}]") + "}"

        info = json.loads(raw_info)

        self.mp3_url = info["file"]["mp3-128"]

        try:
            # Add in http for those times when Bandcamp is rude.
            if self.mp3_url[:2] == "//":
                self.mp3_url = "http:" + self.mp3_url

        except TypeError:
            if not self.silent:
                safe_print(
                    '\n {} is not openly available.'.format(self.title))

                return False

        return True

    def download(self):
        if self.verbose:
            safe_print('\nWriting file to {}'.format(self.output))

        # Clean up the main title.
        clean_title = format_information(
            self.title,
            self.artist,
            self.album,
            self.index
        )

        # Download the file.
        download_file(self.mp3_url, self.output, clean_title +
                      ".mp3", verbose=self.verbose)

        if self.art_enabled:
            s = download_file(self.art_url, self.output,
                              clean_title + self.art_url[-4:])

            if self.verbose:
                if s == 1:
                    safe_print('\nSaved album art to {}/{}{}'.format(
                        self.output, clean_title, self.art_url[-4:]))

                elif s == 2:
                    print('\nArtwork already found.')

                else:
                    print('\nFailed to download the artwork. Error code {}'.format(s))


class Album:

    def __init__(self, url, output, request=None, title=None, artist=None, verbose=False, silent=False, art_enabled=False):
        # Requests and other information can optionally be filled to remove unneccessary
        # operations such as making a request to a URL that has already been fetched
        # by another component.

        self.url = url  # URL to download files from.

        # Output directory to create the new album dir in.
        self.output = output

        # Basic information used when writing tracks.
        self.title = title
        self.artist = artist

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

        # Set if the cover should be downloaded as well.
        self.art_enabled = art_enabled

    def fetch(self):
        if not valid_url(self.url):  # Validate the URL
            if not self.silent:
                print("The supplied URL is not a valid URL.")

            return False

        if not self.request:
            # Make a request to the album URL.
            self.request = request.get(self.url)

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

        # Get the title of the album.
        if not self.title:
            self.title = html.unescape(re.sub(
                '[:*?<>|]', '', string_between(self.content, '<meta name="Description" content=', " by ")[2:]))

        # Get the main artist of the album.
        # Find the artist title of the supplied Bandcamp page.
        if not self.artist:
            try:
                self.artist = html.unescape(string_between(
                    string_between(self.content, "var BandData = {", "}"), 'name : "', '",'))

            except IndexError:
                try:
                    self.artist = html.unescape(string_between(
                        string_between(self.content, "var BandData = {", "}"), 'name: "', '",'))

                except:
                    if self.verbose:
                        print("\nFailed to fetch the band/artist title")

        # Setup the correct output directory name.
        self.output = os.path.join(
            self.output, self.artist + " - " + self.title, "")

        # Create a new album folder if it doesn't already exist.
        if not os.path.exists(self.output):
            os.makedirs(self.output)

        # Retrieve the base page URL.
        self.base_url = "{}//{}".format(str(self.url).split("/")[
            0], str(self.url).split("/")[2])

        # Fetch the album URL.
        self.art_url = string_between(
            self.content, '<a class="popupImage" href="', '">')

        # Split the string and convert it into an array.
        tracks = self.content.split(
            '<table class="track_list track_table" id="track_table">', 1)[1].split('</table>')[0].split("<tr")

        # Iterate over the tracks found and begin traversing the given
        # track's title information and insert the track data in the queue.
        if self.verbose:
            print('\nListing found tracks')

        track_index = 0

        for i, track in enumerate(tracks):
            position = track.find('<a href="/track')

            if position != -1:
                # Find the track's name.
                position = position + len('<a href="/track')
                track_name = ""

                while track[position] != '"':
                    track_name = track_name + track[position]
                    position = position + 1

                if track_name != "":
                    track_index += 1

                    # Print the prepared track.
                    if self.verbose:
                        safe_print(self.base_url + "/track" + track_name)

                    # Create a new track instance with the given URL.
                    track = Track(self.base_url + "/track" + track_name, self.output,
                                  album=self.title, index=track_index, verbose=self.verbose)

                    # Retrive track data and store it in the instance.
                    if track.fetch():

                        # Insert the acquired data into the queue.
                        self.queue.insert(i, track)

        return True

    def download(self):
        if self.verbose:
            safe_print('\nWriting album files to {}'.format(self.output))

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


class Discography:

    def __init__(self, url, output, request=None, title=None, artist=None):
        # Requests and other information can optionally be filled to remove unneccessary
        # operations such as making a request to a URL that has already been fetched
        # by another component.

        self.url = url  # URL to get information from.

        # Basic information used when writing tracks.
        self.artist = artist

        self.queue = []  # Queue array to store album tracks in.

        # Store the album request object for later reference.
        self.request = request
        self.content = None

    def fetch(self):
        if not valid_url(self.url):  # Validate the URL
            print("The supplied URL is not a valid URL.")
            return False

        if not self.request:
            # Make a request to the album URL.
            self.request = request.get(self.url)

        if self.request.status_code != 200:
            print("An error occurred while trying to access your supplied URL. Status code: {}".format(
                self.request.status_code))

            self.request = None

            return False

        # Get the content from the request and decode it correctly.
        self.content = self.request.content.decode('utf-8')

        # Verify that this is an album page.
        if not page_type(self.content) == "discography":
            print("The supplied URL is not a discography page.")

    def download(self):
        pass


class Downloader:
    '''
    Main class of Campdown. This class handles all other Campdown functions and
    executes them depending on the information it is given during initilzation.
    '''

    def __init__(self, url, out=None):
        '''
        Init method of Campdown.

        Args:
            url (str): Bandcamp URL to analyse and download from.
            out (str): relative or absolute path to write to.
        '''

        self.url = url
        self.output = out

        # Downloader relevant data.
        self.request = None
        self.content = None

        # Get the script path in case no output path is specified.
        self.script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '')

        if self.output:
            # Make sure that the output folder has the right path syntax
            if not os.path.isabs(self.output):
                if not os.path.exists(os.path.join(self.script_path, self.output)):
                    os.makedirs(os.path.join(self.script_path, self.output))

                self.output = os.path.join(self.script_path, self.output)

        else:
            # If no path is specified use the absolute path of the main file.
            self.output = self.script_path

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

        # TODO: Add page and discography downloads.

        if pagetype == "track":
            track = Track(self.url, self.output,
                          request=self.request, verbose=True, art_enabled=True)

            track.fetch()
            track.download()

            print("\nFinished track download.")

        elif pagetype == "album":
            album = Album(self.url, self.output,
                          request=self.request, verbose=True, art_enabled=True)

            album.fetch()
            album.download()

            print("\nFinished album download.")

        elif pagetype == "discography":
            print("\nDiscography page detected. Downloading this is not in place yet.")

        else:
            print("Invalid page type. Exiting.")


# Check that this file's main function is not being called from another file.
if __name__ == "__main__":
    try:
        url = sys.argv[1]

    except(IndexError):
        print('\nMissing required URL argument')
        sys.exit(2)

    try:
        out = sys.argv[2]

    except(IndexError):
        out = ""

    downloader = Downloader(url, out)

    try:
        downloader.run()

    except (KeyboardInterrupt):
        print("Exiting program...")
        sys.exit(2)
