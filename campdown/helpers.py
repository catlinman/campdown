
import os
import sys
import re
import math
import platform
import time

from datetime import datetime

import requests


def strike(string):
    """
    Make a string strikethrough but assure that it can be printed.

    Args:
        string (str): string to apply strikethrough to.
    """

    if platform.system() is not "Windows":
        return '\u0336'.join(string) + '\u0336'

    else:
        return "X " + string


def safe_get(url):
    headers = requests.utils.default_headers()

    headers.update = {
        "User-Agent": "campdown/1.46 (+https://github.com/catlinman/campdown)",
        "Accept-Encoding": ", ".join(("gzip", "deflate")),
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    # Make a request to the track URL.
    r = requests.get(url, headers=headers)

    return r


def safe_print(string):
    """
    Print to the console while avoiding encoding errors

    Args:
        string (str): string to print to the console without encoding errors.
    """

    try:
        print(string)

    except UnicodeEncodeError:
        try:
            print(string.encode(
                sys.stdout.encoding, errors="replace").decode())

        except UnicodeDecodeError:
            print(string.encode(
                sys.stdout.encoding, errors="replace"))


def safe_filename(string):
    """
    Convert a string into one without illegal characters for the given filesystem.

    Args:
        string (str): the path to remove illegal characters from.

    Returns:
        new path string without illegal characters.
    """

    string = string.replace('/', '&').replace('\\', '')

    if platform.system() is "Windows":
        string = re.sub('[":*?<>|]', "", string)

    return string


def string_between(string, start, end):
    """
    Returns a new string between the start and end range.

    Args:
        string (str): the string to split.
        start (str): string to start the split at.
        end (str): string to stop the split at.

    Returns:
        new string between start and end.
    """
    try:
        return str(string).split(str(start), 1)[1].split(str(end))[0]

    except IndexError:
        return ""


def format_information(title, artist, album="", index=0):
    """
    Takes in track information and returns everything as a formatted String.

    Args:
        title (str): track title string
        artist (str): track artist string
        album (str): optional track album string
        index (str): optional track number string

    Returns:
        A formatted string of all track information.
    """

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


def short_information(title, index=0):
    """
    Takes in track information and returns everything as a short formatted String.

    Args:
        title (str): track title string
        index (str): optional track number string

    Returns:
        A short formatted string of all track information.
    """

    if " - " in title:
        split_title = str(title).split(" - ", 1)

        if index:
            return "{} {}".format(index, split_title[1])

        else:
            return "{}".format(split_title[1])
    else:
        if index:
            return "{} {}".format(index, title)

        else:
            return title


def valid_url(url):
    """
    Validate a URL and make sure that it has the correct URL syntax.

    Args:
        url (str): URL string to be evaluated.

    Returns:
        True if the URL is valid. False if it is invalid.
    """
    if "http://" not in url and "https://" not in url:
        return False

    return True


def page_type(content):
    """
    Evaluate the request content and identify the type of the page.

    Args:
        content (str): page content to analyse.

    Returns:
        "album" if a track list was detected.
        "discography" if a set of albums and tracks was found.
        "track" if the above do not apply but a Bandcamp page was still identified.
        "none" if the supplied page is not a Bandcamp page.
    """
    if "bandcamp.com" in content:
        if "Digital Album" and "track_list" in content:
            return "album"

        elif 'id="discography"' not in content:
            return "discography"

        else:
            return "track"

    else:
        return "none"

def find_string_indices(content, search):
    """
    Generate a list that contains all the indices of a string occurrences in another.

    Args:
        content (str): string to search within.
        search (str): string to find occurrences of.

    Returns:
        List containing all found indicies after the search string.
    """
    return [ # Use list comprehension for syntactic diabetes.
        # Add the length of the search to the index like before.
        i + len(search) for i in range(len(content))
            if content.startswith(search, i)
    ]

def download_file(url, output, name, force=False, verbose=False, silent=False, sleep=30, timeout=3, max_retries=2):
    """
    Downloads and saves a file from the supplied URL and prints progress
    to the console. Can use ranged requests to make downloads from Bandcamp faster
    in some cases.  Returns 0 if the download failed, 1 if the download was successful
    and 2 if the download file was already found and has the same file size.

    Args:
        url (str): URL to make the request to.
        output (str): absolute folder path to write to.
        name (str): filename with extension to write the content to.
        force (bool): ignores checking if the file already exists.
        verbose (bool): prints status messages as well as download progress.
        silent (bool): if error messages should be ignored and not printed.
        sleep (number): Seconds to sleep between failed requests.
        timeout (number): The maximum time before a request is timed out.
        max_retries (number): The amount of request retries that should be attempted.

    Returns:
        0 if there was an error in this function
        1 if the download and write is successful
        2 if the file already exists
        r.status_code if a connection error occurred
    """

    if verbose:
        safe_print("\nDownloading: {}".format(name))

    # Status variables.
    success = False
    retries = 0

    headers = requests.utils.default_headers()

    headers.update = {
        "User-Agent": "campdown/1.46 (+https://github.com/catlinman/campdown)",
        "Accept-Encoding": ", ".join(("gzip", "deflate")),
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    # Initilize our response variable.
    response = None

    # Make a ranged request which will be used to stream data from.
    while not response and retries < max_retries:
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=timeout)

        except(requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            # Print a status message for this sort of timeout error.
            print("503 Service Unavailable. Attempting {} of {} retries.".format(retries + 1, max_retries))
            print("Waiting for {} seconds ...".format(sleep))

            # Sleep for a large amount of time.
            time.sleep(sleep)
            retries += 1

    # Verify that our response data exists and has a valid status code.
    if response and response.status_code != 200:
        if not silent:
            print("Request error {}".format(response.status_code))

        return response.status_code

    # Get the total length of our remote content. Used for verification and progress calculation. 
    remote_length = response.headers.get('content-length')

    # Fail out if we can't get the data length.
    if remote_length is None:
        if not silent:
            print("Request does not contain an entry for the content length.")

        return 0

    # Convert our raw length to an integer value for further processing.
    remote_length = int(remote_length)

    # This value represents how much as a margin percentage of the local file size
    # can the local file can differ from the remote one before being discarded.
    confidence_percentage = 0.01

    if not force and os.path.isfile(os.path.join(output, name)):
        local_length = os.path.getsize(os.path.join(output, name))

        # Confidence is negative if we're lacking data greater than our margin.
        confidence = -(remote_length - (local_length + (remote_length * confidence_percentage)))

        # If we have less data than our confidence percentage we re-download our file.
        if confidence < 0:
            if verbose:
                print("File already found but the file size does not match up. Re-downloading.")

        else:
            if verbose:
                print("File already found. Skipping download.")

            return 2

    # Reset retries for the new process of iterating content.
    retries = 0

    while not success and retries < max_retries:
        # Open a file stream which will be used to save the output string
        with open(os.path.join(output, safe_filename(name)), "wb") as f:
            # Storage variables used while evaluating the already downloaded data.
            dl = 0
            cleaned_length = int((remote_length * 100) / pow(1024, 2)) / 100
            block_size = 2048

            time_last = datetime.now()

            try:
                for chunk in response.iter_content(chunk_size=block_size):
                    # Add the length of the chunk to the download size and
                    # write the chunk to the file.
                    dl += len(chunk)
                    f.write(chunk)

                    if verbose:
                        # Calculate the the download completion percentage.
                        done = int(50 * dl / remote_length)

                        # Display a bar based on the current download progress.
                        sys.stdout.write(
                            "\r[{}{}{}] {}MB / {}MB ".format(
                                "=" * done,
                                ">",
                                " " * (50 - done),
                                (int(((dl) * 100) / pow(1024, 2)) / 100),
                                cleaned_length
                            )
                        )

                        # Flush the output buffer so we can overwrite the same line.
                        sys.stdout.flush()

                # Verify our download size for completion. Since the file sizes will
                # not entirely match up because of possible ID3 tag differences or
                # additional headers, pass a margin/percentage confidence check instead.
                local_length = os.path.getsize(f.name)

                # Confidence is negative if we're lacking data greater than our margin.
                confidence = -(remote_length - (local_length + (remote_length * confidence_percentage)))

                # Debug lines to help us possibly identify size differential issues.
                # print(
                #     "\nRemote size: {} | Local size: {} | Confidence margin percentage: {:.2%} | Confidence: {}".format(
                #         remote_length,
                #         local_length,
                #         confidence_percentage,
                #         int(-confidence)
                #     )
                # )

                if confidence < 0:
                    # Print a newline to skip the buffer flush.
                    print("")

                    # Print a status message to inform the user of incomplete data.
                    print("The download didn't complete. Attempting {} of {} retries.".format(retries + 1, max_retries))
                    print("Waiting for {} seconds ...".format(sleep))

                    # Sleep for a large amount of time.
                    time.sleep(sleep)
                    retries += 1

                else:
                    # Request and download was successful.
                    success = True

            except(requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                # Print a newline to skip the buffer flush.
                print("")

                # Print a status message for this sort of timeout error.
                print("503 Service Unavailable. Attempting {} of {} retries.".format(retries + 1, max_retries))
                print("Waiting for {} seconds ...".format(sleep))

                # Sleep for a large amount of time.
                time.sleep(sleep)
                retries += 1

    if success:
        if verbose:
            # Print a newline to skip the buffer flush.
            print("")
            
        return 1

    else:
        if verbose:
            # Print a newline to skip the buffer flush.
            print("")

            print("Connection timed out or interrupted.")

        # Remove the possibly partial file and return the correct error code.
        os.remove(os.path.join(output, safe_filename(name)))

        return 0
