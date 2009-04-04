This script (hydroToSf2) is a tool which allows you to convert a
Hydrogen drumkit into a SF2 soundfont. It uses Learjeff's soundfont tools
to do all the hard work.

Requirements:
To use the conversion functions (ie if you have flac or other-then-wav formatted drum samples)
You will need flac and sox in your path.
You'll also need pyxml, and tarfile for python (most people should have these) 

tested on Python 2.4.3 on Ubuntu Dapper Linux
To get what you need there, type:
sudo apt-get install python python-xml flac sox

Quick usage:

Download drumkits from http://www.hydrogen-music.org/?p=drumkits

If it's a .h2kit file, just run the script like this:
./hydroToSf2 filename.h2kit (replace filename.h2kit with the file)

if you want to convert an already-installed (in hydrogen GUI) drumkit do this:
./hydroToSf2 $HOME/.hydrogen/data/kit_name (replace kit_name withe the directory that has the kit.)


What to do with .SF2 file?:

In linux, use swami to look at/play the soundfont.

fluidsynth is a command-line soundfont-loader that works for everybody.
asfxload will load it onto your emu10k1 running alsa
sfxload will load it onto your emu10k1 running OSS.

After it is loaded you can sequence to it with seq24 or rosegarden
or whatever.

Why did I do this?:
I like the tiny overhead of using my souncard's (emu10k1) built-in wavetable
better then loading up hydrogen whenever I need a drum maqchine. Hydrogen is
better then what you get with this, but if you don't need LADSPA effects, humanizing,
or jack capabilities, this is ideal.  I still use hydrogen for recording into
ardour, making midi files to be played in seq24 (much nicer interface) or any time I want it
to sound perfect.



#################################################

Below is the original README from Learjeff's soundfont tools

#################################################
Learjeff's soundfont tools
Copyright 2004, Jeff Learman

No warranties.  Programs are likely to be fragile, especially
when taken outside the narrow range of test scenarios I've used!

Things you'll need:
    A way to capture the wave data (mike, soundcard, etc.)
    A wave editor -- optional but useful for noise reduction or bit
        depth conversion.
    Python, download it from www.python.org and install it.  (Python
        is a scripting language like Perl.)
    A little ability to use the DOS command shell.

Installation:
    Extract all the .py files into a new directory of your choice.
    Put that directory on your executable path, or else you
	can specify the path to the programs explicitly.
    To run build the demo soundfont, you'll need to convert
        the two .mp3 layer sample files in the "demo" directory
        into wave files.  An excellent program for doing this
	is dBPowerAmp Music Converter, found at
	"http://dBPowerAmp.com/dmc.htm".

A note on terminology:
    I'm using the term "layer" only for the purpose of what
    more sensible folks call "velocity splits", meaning a set
    of samples that were recorded with the same key velocity
    (or force or loudness).  I'm NOT using it to refer to
    "layered instruments", where you have two sounds from
    two different instruments when you hit one key.

To build your own soundfont:

 1) Sample the instrument.

    For each velocity layer, sample all keys you'll be sampling
    into a single wave file.  The tools currently don't handle
    two .wav files for the same velocity layer -- if you do end
    up with two, there's a workaround.  (One for the feature list.)
    Ideally, sample in 24 bits.

    You might want to read about layer file names below before
    starting this step.

 2) Prepare the velocity layer files

    De-noise the layer files in your favorite wave editor, such
    as CoolEdit or (free) Audacity.  Then normalize, and convert
    to 16 bit format if they aren't already.  Dithering optional
    but probably best.

    If there are any snarks (sample attempts you don't want to
    keep) that are longer than the minimum sample duration
    (a configurable parameter in jCutSamps.py, defaulting to
    1 sec.), delete them from the layer wave file.  It's better
    to delete them rather than silence them, because the "silence"
    is sampled to help detect the end of a note, and a chunk of
    absolute silence can throw the algorithm off.

    Snarks smaller than the minimum sample duration will be
    automatically ignored by the program.

    Use the following format for the prepared layer file names:

      <prefix>_<layername>.wav

    where <prefix> is anything you want, usually an abbreviation
    for the soundfont or instrument.  <layername> is also anything
    you want, but something that indicates to you what velocity
    the layer file samples were recorded at.

    Examples for different layer file naming conventions:

      using MIDI velocities:
          sf1_v16.wav sf1_v32.wav sf1_v64.wav ...
      using music notation:
          sf1_pp.wav sf1_p.wav sf1_mp.wave sf1_m.wave sf1_mf.wav ...
      using whatever:
          sf1_soft.wav, sf1_medium.wav, sf1_hard.wav, sf1_nuke.wav

    Use anything that's meaningful to you, but the layer names will
    show up later.  The prefix will simply be preserved by the
    program and don't mean anything specific.

 3) Convert the layer files to individual sample files.

    Run jCutSamps.py to chop up the layer files into sample files.
    It produces a set of closely cropped sample files, suitable
    for building into a soundfont.  Furthermore, it names them
    according to this schema:

      <prefix>_<layer>_<notenum>_<notename>.wav

    <prefix> is as described above.
    <layer> is as described above.
    <notenum> is the MIDI note number in the sample, or 000 if
	    it can't tell.
    <notename> is the note name in normal notation, using upper
            case for the note, lower case 'b' to indicate flat,
	    and a one-digit octave number in normal MIDI parlance.

    The program does not handle samples outside the range of an
    88-key piano keyboard.  As you can imagine, it's also not
    intended for percussion instruments and drums where the note
    isn't clear.

    The pitch detection algorithm (auto-correlation) isn't the
    best algorithm, so it's touchy.  Let me know if it tends to
    work or not for your instrument.  It seems to work well for
    acoustic piano and Rhodes.

    It's generally best to put all the samples in a single folder.
    Keep different instruments in different folders.  For this
    example, we'll keep the chopped samples in a "samps" directory,
    and the input wave files in the current directory (along with
    the soundfont and other control files).

    Example:
        mkdir samps
        jCutSamps -f samps sf1_*.wav

    Get a cup of coffee.  This one takes a long time, about 30
    seconds per sample in my sample sets.

    When it's done, inspect the sample names.  If you have samples
    with note number 000, figure out what note they really are
    and name them accordingly.  It's not necessary to get the MIDI
    note number correct -- it's not used by the program.

4)  Configure the keyboard mapping.

    Create a file that's your soundfont name but with a ".sfc" extension,
    for "soundfont control".  See details in the example provided.

5)  Build the keyboard map

    Example:
        jMap.py sf1 samps/*.wav

    This reads the control file (sf1.sfc) and, based on the names of
    the wave files found, creates a key map file (sf1.sfk).
    Take a look at the file it created to see if that's
    how you want your samples mapped.  Adjust accordingly.
    This completes almost immediately.  It does verify that the
    specified sample files exist, but doesn't inspect their contents.
    It trusts the file names to specify the note.

6)  Build the soundfont

    Example, mono soundfonts:
        jMksf.py sf1
    Example, stereo soundfonts:
        jMksf.py -s sf1

    This spends most of its time copying wave data.  It generally
    takes a second or so per sample.

    Bingo, you're done.  Test your soundfont in your favorite player.
    Make any necessary adjustments on the keymap config file and
    run the second two programs again -- just takes a moment.

7)  Resample everything and start over.

    Most likely, you've learned what's not ideal about your sample
    set.  Perhaps you needed more layers, or to sample more keys.
    Adjust the layer definitions (if necessary) and start over.

8)  Touch up the soundfont in a soundfont editor

    Soundfonts have lots of parameters to play with.  Also, if your
    samples aren't full-length, you'll need to loop them.
    I recommend Extreme Sample Converter, at "http://www.extranslator.com",
    which has an excellent loop editor.  Unfortunately, it doesn't adjust
    the velocity map (an important aspect).


Have fun!
Jeff

learjef@aol.com
http://learjeff.com


