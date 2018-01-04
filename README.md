# sapfy
A daemon intended to sap spotify songs into your local library slowly
freeing you from the proprietary hinges. The idea here is not to crack spotify
protection algorithm or anything is just a daemon intended to be the most 'set
it and forget it' possible, and will slowly sap all the songs you hear into
your local disk, until one day, you won't need spotify anymore.

## Features
- **We support both spotify free and premium** - The only difference is that the
    bitrate on spotify free (128kbps VBR) is lower than spotify premium. See
    the next point.
- **Ignores advertisements automatically** - Even in spotify free we wont
    record advertisement to clutter your library. We will even try to skip them,
    since spotify is allowing some ads to be skipped.
- **JACK audio server** - the sky is the limit here, sapfy got the
    left and right ends connected, to whatever source of audio, you do you,
    have fun. Personally I left spotify permanently playing in the background,
    whether I want to listen to music or not I just (un)plug spotify's outputs to 
    the actual physical output.
- **Supports pauses** - You can pause and resume whenever, the final song will
    be intact, no silence, as if it were never paused
- **We can detect corrupted/wrongly recorded/incomplete tracks** - And even 
    delete them if you want.


## Installation
So far, it's a extremely simple proof of concept and assumes a lot of things about your
sound setup, I intend to make it more seamless to more setups, but here is
how to get it working:

- Python 3.6
- A running jack audio server. Mainly for the 'connecting' ability that allows us to isolate spotify's output. There is no *real* need for all that real-time kernels, limits, etc. 
- An exclusive/dedicated jack sink named spotify, on my system I created a 
    pulse-jack sink to represent spotify since on linux spotify outputs to 
    pulseaudio e.g.:
    - On linux it needs an ALSA -> Pulse -> Jack (Plugin) bridged setup. This is mostly because spotify only supports pulseaudio, and this is the only way you are able to create a dedicated output and not to mix spotify output with the rest of the computer sounds. Arch wiki has a good [tutorial](https://wiki.archlinux.org/index.php/PulseAudio/Examples#PulseAudio_through_JACK) on how to setup the two to work together. E.g.:
    - `pactl load-module module-jack-sink client_name=spotify connect=yes`
- Redirect spotify's (only spotify's) output to the newly created, exclusive
    jack source

Given such setup, the script should be able to create a jack output and 
automatically connect it to spotify's jack-pulseaudio sink.

The required dependency are all on requirements.txt you can use pip to install them all. So to sum it all up, this should get you up and running:

```bash
git clone https://github.com/samosaara/sapfy ~/.sapfy
pip install --user -r ~/.sapfy/Requirements.txt 
mkdir -p  ~/.local/bin/
ln -s $HOME/.sapfy/sapfyd ~/.local/bin/sapfy
```
There is now an executable symbolic link to named sapfy inside your `~/.local/bin` that you can use to execute the daemon. That folder might not be on your `PATH`, you may move the executable, or see [here](https://unix.stackexchange.com/a/26059/230047).

## Usage

The way I structured the imports, you need to run the program as a python module if want to run it directly through python
```bash
python3 -m sapfy 
```
You can use --help to see the available command line options.

### The output string
The --output flag receives a string, that will be formatted with the song's current metadata. It must not have the file extension, it will be added automatically. The output string can have the following place-holders that will be replaced based on the track metadata:

| Property | Type | Description |
| --- | --- | --- |
| title | String | The track's title |
| artist | String List | An zero indexed array containing all the artists involved in the particular song. |
| album | String | String with the name of the track's album. |
| trackNumber | Integer | The number of this song on the current disc. |
| albumArtist | String List | String with the name of the artist behind the track's album. |
| autoRating | Float | Number from 0 to 5 indicating spotify's grade. |
| discNumber | Integer | Which of the album's disc(s) is the track at.  |
| length | Integer | Number of seconds this track has. |

For an example, the default output string is

```python
"{albumArtist[0]}/{album}/{trackNumber} {title}'"
```
