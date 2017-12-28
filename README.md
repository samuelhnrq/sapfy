# sapfy
A daemon intended to sap spotify songs into your local library slowly
freeing you from the propietary hinges.

## Usage
So far, it's a extremely simple POC and assumes a lot of things about your
sound setup, I intend to make it more seamless to more setups, but here is
how to get it working:

- A running jack server (mine is running in realtime not sure if matters)
- Alsa -> Pulse -> Jack (Plugin) bridged setup. This is mostly because spotify 
only supports pulseaudio as far as I can tell, and this is the only way you are
able to create a dedicated output not to mix spotify output with the rest of the
computer sounds. Arch wiki has a good [tutorial](https://wiki.archlinux.org/index.php/PulseAudio/Examples#PulseAudio_through_JACK) on how to setup the two to work together.
- An excluse/dedicated jack-pulse sink named spotify e.g.:
    - `pactl load-module module-jack-sink client_name=spotify connect=yes`
- Redirect spotify's (only spotify) output to the newly created, exclusive
    pulseaudio sink

Given such setup, the script should be able to create a jack output and 
automatically connect it to spotify's jack-pulseaudio sink.

The required dependency are all on requirements.txt you can use pip to install
them all. e.g.:

```
pip install --user -r Requirements.txt 
```
