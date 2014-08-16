import os
import math
import sys
import requests
import json

# TODO: - Add album dowloading
#       - Handle multiple downloads in a queue
#       - Add a fancy GTK GUI

# Currently includes sucky argument passing. Will clean this up later on.

try:
    bandcamp_track_url = sys.argv[1].replace('\\', '/')
except:
    print('\nMissing required URL argument')
    sys.exit(2)

try:
    outputfolder = sys.argv[2].replace('\\', '/')
    if outputfolder[-1] != "/":
        outputfolder = str(outputfolder) + "/"
except:
    outputfolder = os.path.dirname(__file__) + "/"

print('\n' + "Writing all output files to '%s[ALBUMNAME]'" % outputfolder)

r = requests.get(bandcamp_track_url).content
raw_json = ("{" + (str(r).split("trackinfo: [{",1)[1].split("}]")[0]) + "}")
clean_json = json.loads(raw_json)

track = clean_json["track_num"]
title = clean_json["title"]
duration = clean_json["duration"]
fileurl = clean_json["file"]["mp3-128"]

print('\nFetched URL from %s' % fileurl)

with open(outputfolder + title + ".mp3", "wb") as f:

        print('\n' + "Downloading: " + title)
        response = requests.get(fileurl, stream = True)
        total_length = response.headers.get('content-length')

        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            cleaned_length = int((total_length * 100) / pow(1024,2)) / 100
           
            for data in response.iter_content():
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s%s] %sMB / %sMB " % ('=' * done, ">",' ' * (50 - done), (int(((dl) * 100) / pow(1024,2)) / 100), cleaned_length))
                sys.stdout.flush()

print('\n\n Finished downloading all tracks')