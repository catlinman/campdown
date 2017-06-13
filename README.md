
# Campdown #

Campdown is a utility that can be used to automate downloading of tracks and
albums from Bandcamp. It requires the Python interpreter, version 3.4+ and is
not platform specific.

## Setup ##

Campdown can be installed allowing you to directly run the `campdown` command.
This also installs any dependencies the script might have.

    $ python3 setup.py install

If you don't want to use the setup but would like to still use the script
directly or intend to use it within your project you will have to still install
*requests*, *mutagen* and *docopt* which you can download using *pip*.

    $ pip install -r requirements.txt

To run Campdown simply execute the following command.

    $ campdown <Track, album or discography URL>

If you want to use the CLI without the setup you can run the *campdown.py*
script in the project root directory. Make sure to have dependencies installed
beforehand.

## Notice ##

Campdown allows you to download tracks that are openly available on each of
Bandcamp's sub-domains. Keep in mind that these can be accessed without using
any special tools. Campdown only automates the otherwise tedious process of
searching each page's code for the link to the given file.

This however also means that the downloaded tracks only come with a low bitrate
of 128kbit/s. This is probably to reduce traffic while viewing and listening to
the songs that are openly available.

If you want the full quality of a given track you will have to buy it from
Bandcamp as you usually would. Also, if you like a song or album you should
probably think about supporting the artist/band.

## License ##

This repository is released under the MIT license. For more information please
refer to [LICENSE](https://github.com/catlinman/campdown/blob/master/LICENSE)
