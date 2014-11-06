# Campdown #

Campdown is a utility that can be used to automate downloading of tracks and albums from Bandcamp. It requires the Python interpreter, version 3.4+ and is not platform specific.

## Setup ##

To run Campdown, simply open up the Python interpreter or run the script in your native shell using the following command. Windows users should in this case make sure that they have their Python installation folder added to their PATH variable. The same goes for Python's script folder which contains *pip* by default.

    $ python campdown.py [Track or album URL] [Output folder location]

Campdown requires *requests* which you can download using *pip*.

    $ pip install requests

## Notice ##

Campdown allows you to download tracks that are openly available on each of Bandcamp's sub-domains. Keep in mind that these can be accessed without using any special tools. Campdown only automates the otherwise tedious process of searching each page's code for the link to the given file.

This however also means that the downloaded tracks only come with a low bitrate of 128kbit/s. This is probably to reduce traffic while viewing and listening to the songs that are openly available.

If you want the full quality of a given track you will have to buy it from Bandcamp as you usually would. Also, if you like a song or album you should probably think about supporting the artist/band.

## Licence ##

This repository is released under the MIT license. For more information please refer to [LICENSE](https://github.com/Catlinman/Campdown/blob/master/LICENSE)
