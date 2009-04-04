
import math

mnote_names_flat = [
  "xx", "xx",  "xx", "xx",  "xx", "xx", "xx",  "xx", "xx",  "xx", "xx",  "xx",
  "xx", "xx",  "xx", "xx",  "xx", "xx", "xx",  "xx", "xx",  "A0", "Bb0", "B0",
  "C1", "Db1", "D1", "Eb1", "E1", "F1", "Gb1", "G1", "Ab1", "A1", "Bb1", "B1",
  "C2", "Db2", "D2", "Eb2", "E2", "F2", "Gb2", "G2", "Ab2", "A2", "Bb2", "B2",
  "C3", "Db3", "D3", "Eb3", "E3", "F3", "Gb3", "G3", "Ab3", "A3", "Bb3", "B3",
  "C4", "Db4", "D4", "Eb4", "E4", "F4", "Gb4", "G4", "Ab4", "A4", "Bb4", "B4",
  "C5", "Db5", "D5", "Eb5", "E5", "F5", "Gb5", "G5", "Ab5", "A5", "Bb5", "B5",
  "C6", "Db6", "D6", "Eb6", "E6", "F6", "Gb6", "G6", "Ab6", "A6", "Bb6", "B6",
  "C7", "Db7", "D7", "Eb7", "E7", "F7", "Gb7", "G7", "Ab7", "A7", "Bb7", "B7",
  "C8", "Db8", "D8", "Eb8", "E8", "F8", "Gb8", "G8", "Ab8", "A8", "Bb8", "B8",
  "C9", "Db9", "D9", "Eb9", "E9", "F9", "Gb9", "G9", "Ab9", "A9", "Bb9", "B9"]

mnote_names_sharp = [
  "xx", "xx",  "xx", "xx",  "xx", "xx", "xx",  "xx", "xx",  "xx", "xx",  "xx",
  "xx", "xx",  "xx", "xx",  "xx", "xx", "xx",  "xx", "xx",  "A0", "A#0", "B0",
  "C1", "C#1", "D1", "D#1", "E1", "F1", "F#1", "G1", "G#1", "A1", "A#1", "B1",
  "C2", "C#2", "D2", "D#2", "E2", "F2", "F#2", "G2", "G#2", "A2", "A#2", "B2",
  "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
  "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
  "C5", "C#5", "D5", "D#5", "E5", "F5", "F#5", "G5", "G#5", "A5", "A#5", "B5",
  "C6", "C#6", "D6", "D#6", "E6", "F6", "F#6", "G6", "G#6", "A6", "A#6", "B6",
  "C7", "C#7", "D7", "D#7", "E7", "F7", "F#7", "G7", "G#7", "A7", "A#7", "B7",
  "C8", "C#8", "D8", "D#8", "E8", "F8", "F#8", "G8", "G#8", "A8", "A#8", "B8",
  "C9", "C#9", "D9", "D#9", "E9", "F9", "F#9", "G9", "G#9", "A9", "A#9", "B9"]

mnote_names = mnote_names_flat

def mnote_name(mnote, pad="_"):
    if mnote > len(mnote_names) - 1:
        return "xx"
    name = mnote_names[mnote]
    if pad:
        name = name.rjust(3).replace(" ", pad)
    return name

def midi_note_for_freq(freq, pad="_"):
    abs_cents = int(1200 * math.log(freq/220.0,2) + 5700.0)
    mnote = int((abs_cents + 50) / 100)
    cents = int((abs_cents + 50) % 100) - 50
    name = mnote_name(mnote)
    if pad:
        name = name.rjust(3).replace(" ", pad)
    return (mnote, name, cents)

# return note name given either MIDI note number or name

def notename(note):
    if len(note) < 2:
        return None

    if "A" <= note[0] <= "G":
        if note[1] == "b" or note[1] == "#":
	    if len(note) != 3:
	        return None
	elif len(note) > 2:
	    return None
	return note

    # Not a name, might be a number

    try:
        num = int(note)
    except:
        return None

    return mnote_name(num, pad=None)

# return MIDI note given either number or name

def notenum(note):
    # get it as a name
    name = notename(note)
    if not name:
        return None

    if name in mnote_names_flat:
	return mnote_names_flat.index(name)
    if name in mnote_names_sharp:
	return mnote_names_sharp.index(name)
    return None


if __name__ == "__main__":

    import sys
    args = sys.argv

    if len(args) < 2:
        print "usage: %s {<note>} -- print MIDI note name/number" % args[0]
	print
	print "  If the argument is a number, it prints the name,"
	print "  and vice-versa."
	sys.exit(1)

    while len(args) > 1:
	arg = args[1]
	del args[1]

	print arg, "=", notename(arg), notenum(arg)


