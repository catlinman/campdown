import os
import math
import sys
import re
import requests
import json

if __name__ == "__main__":
    try:
        try:
            bandcamp_url = sys.argv[1].replace('\\', '/')
            bandcamp_url = sys.argv[1].replace('"', '')
        except:
            print('\nMissing required URL argument')
            sys.exit(2)

        try:
            outputfolder = sys.argv[2].replace('\\', '/')
            if outputfolder[-1] != "/":
                outputfolder = str(outputfolder) + "/"
        except:
            outputfolder = os.path.dirname(__file__).replace('\\', '/') + "/"

        try:
            r = requests.get(bandcamp_url).content
        except:
            print("An error occurred while trying to access your supplied URL")

        bandcamp_base_url = str(bandcamp_url).split(".com", 1)[0] + ".com"
        bandcamp_isAlbum = False
        bandcamp_queue = []
        bandcamp_band = ""

        try:
            bandcamp_band = str(r).split("var BandData = {",1)[1].split("}")[0].split('name : "')[1].split('",')[0]
        except IndexError:
            try:
                bandcamp_band = str(r).split("var BandData = {",1)[1].split("}")[0].split('name: "')[1].split('",')[0]
            except:
                print("\nFailed to fetch the band title")

        if str(r).find("track_list") == -1:
            rawinfo = ("{" + (str(r).split("trackinfo: [{",1)[1].split("}]")[0]) + "} ").replace('\\n', ' ').replace('\\', ' ')
            trackinfo = json.loads(rawinfo)
            bandcamp_queue.insert(1, trackinfo)

            bandcamp_isAlbum = False
            bandcamp_album = str(r).split('<span itemprop="name">')[1].split("</span>")[0]

        else:
            bandcamp_isAlbum = True
            bandcamp_album = str(r).split('<meta name="Description" content=')[1].split(" by ")[0][3:]

            if not os.path.exists(outputfolder + "/" + bandcamp_album + "/"):
                print('\nCreated album folder in %s' % (outputfolder + bandcamp_album + "/"))
                os.makedirs(outputfolder + "/" + bandcamp_album + "/")

            bandcamp_album_tracktable = str(r).split('<table class="track_list track_table" id="track_table">',1)[1].split('</table>')[0]
            bandcamp_album_tracks = bandcamp_album_tracktable.split("<tr")

            print('\nListing found tracks')
            for i, track in enumerate(bandcamp_album_tracks):
                position = track.find('<a href="/track')
                
                if position != -1:
                    position = position + len('<a href="/track')
                    trackname = ""
                    while track[position] != '"':
                        trackname = trackname + track[position]
                        position = position + 1

                    if trackname != "":
                        print("" + bandcamp_base_url + "/track" + trackname)

                        track_r = requests.get(bandcamp_base_url + "/track" + trackname).content
                        rawinfo = ("{" + (str(track_r).split("trackinfo: [{",1)[1].split("}]")[0]) + "} ").replace('\\n', ' ').replace('\\', ' ')
                        trackinfo = json.loads(rawinfo)
                        bandcamp_queue.insert(i, trackinfo)

        if bandcamp_isAlbum == True:
            outputfolder = outputfolder + bandcamp_album

        print("Writing all output files to %s" % outputfolder)

        for i in range(0, len(bandcamp_queue)): 
            title = bandcamp_queue[i]["title"]
            duration = bandcamp_queue[i]["duration"]
            url = bandcamp_queue[i]["file"]["mp3-128"]

            if title.find(" - ") != -1:
                partialtitle = str(title).split("-", 1)

                if bandcamp_isAlbum == True:
                    title = partialtitle[0] + "- " + bandcamp_album + " - " + str(i + 1) + partialtitle[1]
                else:
                    title = partialtitle[0] + "- " + bandcamp_album + " -" + partialtitle[1]
            else:
                if bandcamp_isAlbum == True:
                    title = bandcamp_band + " - " + bandcamp_album + " - " + str(i + 1) + " " + title
                else:
                    title = bandcamp_band + " - " + bandcamp_album + " - " + title

            if os.path.isfile(outputfolder + "/" + title + ".mp3") == False:
                try:
                    with open(outputfolder + "/" + title + ".mp3", "wb") as f:

                        print('\n\n' + "Downloading: " + title)
                        response = requests.get(url, stream = True)
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
                except (KeyboardInterrupt, SystemExit):
                    print('\n\nDownload aborted - removing download remnants')
                    os.remove(outputfolder + "/" + title + ".mp3")

                    try:
                        os.rmdir(outputfolder)
                    except OSError:
                        print()

                    sys.exit(2)
            else:
                print("Skipping  %s" % title)
            
        print('\n\nFinished downloading all tracks')

    except (KeyboardInterrupt, SystemExit):
        print("Program interrupted by user - exiting")
