This script (hydroToSf2) is a tool which allows you to convert a
Hydrogen drumkit into a SF2 soundfont. It uses Learjeff's soundfont tools
to do all the hard work.

## Requirements: ##
To use the conversion functions (ie if you have flac or other-then-wav formatted drum samples)
You will need flac and sox in your path.
You'll also need pyxml, and tarfile for python (most people should have these)

tested on Python 2.4.3 on Ubuntu Dapper Linux and Python 2.5.2 on Intrepid
To get what you need there, type:
sudo apt-get install python python-xml flac sox

## Quick usage: ##

Download drumkits from http://www.hydrogen-music.org/?p=drumkits

If it's a .h2kit file, just run the script like this:
```
./hydroToSf2 filename.h2kit (replace filename.h2kit with the file)
```
if you want to convert an already-installed (in hydrogen GUI) drumkit do this:
```
./hydroToSf2 $HOME/.hydrogen/data/kit_name
```
or
```
./hydroToSf2 /usr/share/hydrogen/data/drumkits/kit_name
```
(replace kit\_name withe the directory that has the kit.)


## What to do with .SF2 file?: ##

In linux, use swami to look at/play the soundfont.

fluidsynth is a command-line soundfont-loader that works for everybody.
asfxload will load it onto your emu10k1 running alsa
sfxload will load it onto your emu10k1 running OSS.

Lately, I have been using linuxsampler.  I wanted gig files for my soundfonts, too.  I couldn't find any native linux program (maybe I'll write a script for that, too.) So, I had to use awave studio pro in VirtualBox (the output format I used was 1.x compressed Gigastudio.) A couple of the SF2 files had little errors, and I didn't have time to investigate, but the gig file has most of the hydrogen kits, except these.

I heard that [Translator](http://www.chickensys.com/downloads/translator_free.php) can do this, and it runs in wine, so this might be another temporary option.

After it is loaded you can sequence to it with seq24 or rosegarden
or whatever.

## Why did I do this?: ##
I like the tiny overhead of using my souncard's (emu10k1) built-in wavetable
better then loading up hydrogen whenever I need a drum machine. Hydrogen is
better then what you get with this, but if you don't need inline LADSPA effects, humanizing, etc, this is ideal.

I also like using a single sampler to do all the work. Linuxsampler and fluidsynth have nice frontends, but also can be run command-line, which is also nice for a headless soundfont player.