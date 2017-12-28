# sapfy
A daemon intended to sap spotify songs into your local library slowly
freeing you from the propietary hinges. The idea here is not to crack spotify
protection algorhytm or anything is just a daemon intended to be the most 'set
it and forget it' possible, and will slowly sap all the songs you hear into
your local disk, until one day, you won't need spotify anymore.

## Installation
So far, it's a extremely simple POC and assumes a lot of things about your
sound setup, I intend to make it more seamless to more setups, but here is
how to get it working:

- Python 3.6
- A running jack server (mine is running in realtime not sure if matters)
on how to setup the two to work together.
- An excluse/dedicated jack sink named spotify, on my system I created a 
pulse-jack sink to represent spotify since on linux spotify outputs to 
pulseaudio e.g.:
    - On linux it needs an Alsa -> Pulse -> Jack (Plugin) bridged setup. This is mostly because spotify only supports pulseaudio as far as I can tell, and this is the only way you areable to create a dedicated output not to mix spotify output with the rest of thecomputer sounds. Arch wiki has a good [tutorial](https://wiki.archlinux.org/index.php/PulseAudio/Examples#PulseAudio_through_JACK) 
    - `pactl load-module module-jack-sink client_name=spotify connect=yes`
- Redirect spotify's (only spotify) output to the newly created, exclusive
jack source

Given such setup, the script should be able to create a jack output and 
automatically connect it to spotify's jack-pulseaudio sink.

The required dependency are all on requirements.txt you can use pip to install
them all. e.g.:

```bash
pip install --user -r Requirements.txt 
```

## Usage

The way I structured the imports, you need to run the program as a python module
```bash
python3 -m sapfy
```
You can use --help to see the available command line options.

### The output string
Is a string, that will be formatted with the song's current metadata. It must not have the file extension, it will be added automatically. The output string can have the following place-holders that will be replaced based on the track metadata:

| Property | Type | Description |
| --- | --- | --- |
| title | String | The track's title |
| artist | String List | An zero indexed array containing all the artists involved in the particular song. |
| album | String | String with the name of the track's album. |
| trackNumber | Integer | The number of this song on the current disc. |
| albumArtist | String List | String with the name of the artist behind the track's album. |
| autoRating | Float | Number from 0 to 5 indicating spotify's grade. |
| discNumber | Integer | Which of the album's disc(s) is the track at.  |
| lenght | Integer | Number of seconds this track has. |

For an example, the default output string is

```python
"{albumArtist[0]}/{album}/{trackNumber} {title}'"
```
