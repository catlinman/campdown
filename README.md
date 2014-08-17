# Campdown #

Campdown is a utility that can be used to automate downloading of tracks and albums from Bandcamp. It requires the Python interpreter, version 3.4+ and is not platform specific.

## Usage ##

To run Campdown, simply open up the Python interpreter or run the script in your native shell using the following command. Windows users should in this case make sure that they have their Python installation folder added to their PATH variable. The same goes for Python's script folder which contains *pip* by default.

    python campdown.py [Track or album URL] [Output folder location]

Campdown requires *requests* which you can download using *pip*.

    pip install requests

## Licence ##

This repository is released under the MIT license. For more information please refer to [LICENSE](https://github.com/Catlinman/Campdown/blob/master/LICENSE)
