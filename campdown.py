#!/usr/bin/env python

import os
import sys
import math
import re
import json
import html
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
    return string.split(start, 1)[1].split(end)[0]


def format_information(track_title, track_artist, track_album="", track_number=0):
    '''
    Takes in track information and returns everything as a formatted String.

    Args:
        track_title (str): track title string
        track_artist (str): track artist string
        track_album (str): optional track album string
        track_number (str): optional track number string

    Returns:
        A formatted string of all track information.
    '''

    if " - " in track_title:
        split_title = str(track_title).split(" - ", 1)

        if track_album:
            if track_number:
                return "{} - {} - {} {}".format(split_title[0], track_album, track_number, split_title[1])

            else:
                return "{} - {} - {}".format(split_title[0], track_album, split_title[1])

        else:
            if track_number:
                return "{} - {} {}".format(split_title[0], track_number, split_title[1])

            else:
                return "{} - {}".format(split_title[0], split_title[1])
    else:
        if track_album:
            if track_number:
                return "{} - {} - {} {}".format(track_artist, track_album, track_number, track_title)

            else:
                return "{} - {} - {}".format(track_artist, track_album, track_title)

        else:
            if track_number:
                return "{} - {} {}".format(track_artist, track_number, track_title)

            else:
                return "{} - {}".format(track_artist, track_title)


def download_file(url, output_folder, output_name, force=False, verbose=False):
    '''
    Downloads and saves a file from the supplied URL and prints progress
    to the console. Uses ranged requests to make downloads from Bandcamp faster.
    Returns 0 if the download failed, 1 if the download was successfull and 2 if
    the download file was already found and has the same file size.

    Args:
        url (str): URL to make the request to.
        output_folder (str): absolute folder path to write to.
        output_name (str): filename with extension to write the content to.
        force (bool): ignores checking if the file already exists.
        verbose (bool): prints status messages as well as download progress.

    Returns:
        1 if the download and write is successfull
        2 if the file already exists
        r.status_code if a connection error occurred
    '''

    if verbose:
        safe_print('\nDownloading: {}'.format(output_name))

    # Get the size of the remote file through a streamed request.
    r = requests.get(url, stream=True)

    if r.status_code != 200:
        if verbose:
            print("Request error {}".format(r.status_code))

        return r.status_code

    total_length = r.headers.get('content-length')

    if not force:
        if os.path.isfile(os.path.join(output_folder, output_name)):
            if int(os.path.getsize(os.path.join(output_folder, output_name))) != int(total_length):
                if verbose:
                    print(
                        'File already found but the file size doesn\'t match up. Redownloading.')

            else:
                if verbose:
                    print('File already found. Skipping download.')

                return 2

    # Open a file stream which will be used to save the output string
    with open(output_folder + "/" + re.sub('[\\/:*?<>|]', "", output_name), "wb") as f:
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

        # Insert a new line to improve console formatting.
        if verbose:
            print()

    return 1


class Campdown:
    '''
    Main class of the Campdown Bandcamp downloader.
    '''

    def __init__(self, url, out):
        '''
        Init method of Campdown.

        Args:
            url (str): Bandcamp URL to analyse and download from.
            out (str): relative or absolute path to write to.
        '''
        self.artist = ""
        self.album = ""
        self.track = ""

        self.is_album = False
        self.is_mainpage = False

        self.queue = []

        self.url = url
        self.output = out

        self.script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '')

        if not "http://" in self.url and not "https://" in self.url:
            print('\n%s is not a valid URL' % self.url)
            sys.exit(2)

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

        # Get the content from the supplied Bandcamp URL.
        main_request = requests.get(self.url)
        main_content = main_request.content.decode('utf-8')

        if main_request.status_code != 200:
            print("An error occurred while trying to access your supplied URL. Status code: {}".format(
                main_request.status_code))

            return

        # Retrieve the base page URL, fetch the album art URL and create
        # variables which will be used later on.
        self.base_url = "{}//{}".format(str(self.url).split("/")[
            0], str(self.url).split("/")[2])

        self.art_url = string_between(
            main_content, '<a class="popupImage" href="', '">')

        # Find the artist name of the supplied Bandcamp page.
        try:
            self.artist = html.unescape(string_between(
                string_between(str(main_content), "var BandData = {", "}"), 'name : "', '",'))

        except IndexError:
            try:
                self.artist = html.unescape(string_between(
                    string_between(str(main_content), "var BandData = {", "}"), 'name: "', '",'))

            except:
                print("\nFailed to fetch the band/artist title")

        # We check if the page has a track list or not. If not, we only fetch
        # the track info for the one track on the given Bandcamp page.
        if not "track_list" in str(main_content):
            # Extract the unformatted JSON array from the request's content.
            # Convert it to an actual Python array afterwards.
            raw_info = "{" + \
                string_between(str(main_content),
                               "trackinfo: [{", "}]") + "}"

            track_info = json.loads(raw_info)

            # Insert the track data into the queue and inform the downloader
            # that it's not an album.
            self.queue.insert(1, track_info)

            # Add the name of the album this single track might belong to, to
            # the information that will make up the output filename.
            try:
                self.album = html.unescape(string_between(
                    main_content, '<span itemprop="name">', "</span>"))

            except IndexError:
                self.album = ""

        else:
            # Since the supplied URL was detected to be an album URL, we
            # extract the name of the album.
            self.album = html.unescape(re.sub(
                '[:*?<>|]', '', string_between(str(main_content), '<meta name="Description" content=', " by ")[2:]))

            # Flag output to write to a folder since we have multiple files.
            is_album = True

            # Create a new album folder if it doesn't already exist.
            if not os.path.exists(os.path.join(self.output, self.artist + " - " + self.album)):
                safe_print('\nCreated album folder in {}{} - {}{}'.format(
                    self.output, self.artist, self.album, "/"))

                os.makedirs(self.output + "/" + self.artist +
                            " - " + self.album + "/")

            # Extract the string of tracks from the request's response content.
            # Convert the individual titles to single entries for use in an
            # array.
            album_tracktable = str(main_content).split(
                '<table class="track_list track_table" id="track_table">', 1)[1].split('</table>')[0]

            album_tracks = album_tracktable.split("<tr")

            # Iterate over the tracks found and begin traversing the given
            # track's title information.
            print('\nListing found tracks')

            for i, track in enumerate(album_tracks):
                position = track.find('<a href="/track')

                if position != -1:
                    # Find the track's name.
                    position = position + len('<a href="/track')
                    track_name = ""

                    while track[position] != '"':
                        track_name = track_name + track[position]
                        position = position + 1

                    if track_name != "":
                        print(self.base_url + "/track" + track_name)

                        # Make a single request to the track's own URL and
                        # extract the track info from there.
                        track_request = requests.get(
                            self.base_url + "/track" + track_name).content.decode('utf-8')

                        raw_info = "{" + string_between(
                            str(track_request), "trackinfo: [{", "}]") + "}"

                        track_info = json.loads(raw_info)

                        # Insert the acquired data into the queue.
                        self.queue.insert(i, track_info)

        if self.is_album:
            # Since we know that the downloader is fetching an album we might
            # as well sum up the output string for easier encoding.
            self.output = self.output + self.artist + " - " + self.album

        safe_print(
            '\nWriting all output files to {}'.format(self.output))

        # Store the track index in case it's an album queue.
        track_index = 0

        # Start the process of downloading files from the queue.
        for i in range(0, len(self.queue)):

            if self.is_album:
                track_index += 1

            # Get the title of the current queue-item.
            self.track = format_information(
                self.queue[i]["title"].replace('"', ''), self.artist, self.album, track_index)

            try:
                # Retrieve the MP3 file URL from the queue-item.
                url = self.queue[i]["file"]["mp3-128"]

                # Add in http for those times when Bandcamp is rude.
                if url[:2] == "//":
                    url = "http:" + url

            except TypeError:
                safe_print(
                    '\n {} is not openly available - skipping track'.format(title))

            # Download the file.
            download_file(url, self.output, self.track +
                          ".mp3", verbose=True)

        print('\nFinished downloading all tracks')

        print('\nDownloading artwork...')

        # Make sure that the album art actually exists. Write it to a file.
        filename = ""

        if self.is_album:
            filename = "cover"

        else:
            filename = self.track

        s = download_file(self.art_url, self.output,
                          filename + self.art_url[-4:])

        if s == 1:
            safe_print('Saved album art to {}/{}{}'.format(
                self.output, filename, self.art_url[-4:]))

        elif s == 2:
            print('Artwork already found.')

        else:
            print('Failed to download the artwork. Error code {}'.format(s))


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

    c = Campdown(url, out)

    try:
        c.run()

    except (KeyboardInterrupt):
        print("Exiting program...")
        sys.exit(2)
