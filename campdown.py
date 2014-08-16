import os
import math
import sys
import requests
import json

# TODO: - Add album dowloading
#       - Handle multiple downloads in a queue
#       - Add a fancy GTK GUI

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

bandcamp_base_url = str(bandcamp_track_url).split(".com", 1)[0] + ".com"
bandcamp_album = ""

r = requests.get(bandcamp_track_url).content
print(r)
full_json = []

if str(r).find("track_list") == -1:
    raw_json = ("{" + (str(r).split("trackinfo: [{",1)[1].split("}]")[0]) + "} ")
    track_json = json.loads(raw_json)
    full_json.insert(1, track_json)

else: 
    bandcamp_album = str(r).split('<meta name="Description" content=')[1].split(" by ")[0][3:]

    if not os.path.exists(outputfolder + "/" + bandcamp_album + "/"):
        print('Created album folder in %s' % (outputfolder + "/" + bandcamp_album + "/"))
        os.makedirs(outputfolder + "/" + bandcamp_album + "/")

    # Split up each track's link and retrieve the json from the given track's page.

totaltracks = len(full_json)

print('' + "Writing all output files to %s%s" % (outputfolder, bandcamp_album))

for i in range(0, totaltracks): 
    track = i
    title = full_json[i]["title"]
    duration = full_json[i]["duration"]

    if bandcamp_album != "":
        partialtitle = str(title).split("-", 1)
        title = partialtitle[0] + " - " + bandcamp_album + " - " + str(i) + partialtitle[1]

    fileurl = full_json[i]["file"]["mp3-128"]

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