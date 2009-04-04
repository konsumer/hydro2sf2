#!python
#
# build or dump a soundfont
#
# In progress: stereo samples (works!)
# Note: stereo sf with some mono files not yet tested.
#       I bet it takes as much room as fully stereo sf.
#       Would be nice but not trivial to fix this, but
#       currently, the odd/even-ness of sample idices
#       is used to distinguish left from right.  I'd have
#       to put the concept of stereo & left/right in at
#       a more fundamental level.
#
#       self.stereo also used to calculate number of zones.
#       Would have to actually iterate through zones to
#       count them. IGEN_PER_ZONE would no longer work.

DEBUG = False

LOOP_FOR_SFZ = False	# whether to loop at the end to overcome sfz bug

import sys
import time
import math

import jriff
import jwave
from   jtype import *

generalcontrollers = (
  (0,  "NoController"),
  (2,  "NoteOnVelocity"),
  (3,  "NoteOnKeyNumber"),
  (10, "PolyPressure"),
  (13, "ChannelPressure"),
  (14, "PitchWheel"),
  (16, "PitchWheelSensitivity"),
  )

modtranstypes = (
  (0,	"linear"),
  )

modtypes = (
  (0,	"linear"),
  (1,	"concave"),
  (2,	"convex"),
  (3,	"switch"),
  )

samplinkvals = (
  (1,      "monoSample",	),
  (2,      "rightSample",	),
  (4,      "leftSample",	),
  (8,      "linkedSample",	),
  (0x8001, "RomMonoSample",	),
  (0x8002, "RomRightSample",	),
  (0x8004, "RomLeftSample",	),
  (0x8008, "RomLinkedSample",	),
  )

genvals = (
  ( 0, "startOffset"		), 
  ( 1, "endOffset"		), 
  ( 2, "stLoopOffset"		), 
  ( 3, "endloopAddrsOffset"	), 
  ( 4, "startCoarseOffset"	), 
  ( 5, "modLfoToPitch"		), 
  ( 6, "vibLfoToPitch"		), 
  ( 7, "modEnvToPitch"		), 
  ( 8, "initFFc"		), 
  ( 9, "initFQ"			), 
  ( 10, "modLfoToFilterFc"	), 
  ( 11, "modEnvToFilterFc"	), 
  ( 12, "endAddrsCoarseOffset"	), 
  ( 13, "modLfoToVolume"	), 
  ( 14, "unused1"		), 
  ( 15, "chorusEffectsSend"	), 
  ( 16, "reverbEffectsSend"	), 
  ( 17, "pan"			), 
  ( 18, "unused2"		), 
  ( 19, "unused3"		), 
  ( 20, "unused4"		), 
  ( 21, "delModLFO"		), 
  ( 22, "freqModLFO"		), 
  ( 23, "delVibLFO"		), 
  ( 24, "freqVibLFO"		), 
  ( 25, "delModEnv"		), 
  ( 26, "attModEnv"		), 
  ( 27, "holdModEnv"		), 
  ( 28, "decayModEnv"		), 
  ( 29, "susModEnv"		), 
  ( 30, "relModEnv"		), 
  ( 31, "keynumToModEnvHold"	), 
  ( 32, "keynumToModEnvDecay"	), 
  ( 33, "delVolEnv"		), 
  ( 34, "attVolEnv"		), 
  ( 35, "holdVolEnv"		), 
  ( 36, "decayVolEnv"		), 
  ( 37, "susVolEnv"		), 
  ( 38, "relVolEnv"		), 
  ( 39, "keynumToVolEnvHold"	), 
  ( 40, "keynumToVolEnvDecay"	), 
  ( 41, "instrument"		), 
  ( 42, "reserved1"		), 
  ( 43, "kRange"		), 
  ( 44, "vRange"		), 
  ( 45, "stLoopCoarseOff"	), 
  ( 46, "keynum"		), 
  ( 47, "velocity"		), 
  ( 48, "initAtten"		), 
  ( 49, "reserved2"		), 
  ( 50, "endLoopCoarseOffset"	), 
  ( 51, "coarseTune"		), 
  ( 52, "fTune"			), 
  ( 53, "sampID"		), 
  ( 54, "sModes"		), 
  ( 55, "reserved3"		), 
  ( 56, "scTuning"		), 
  ( 57, "exclusiveClass"	), 
  ( 58, "overridingRootKey"	), 
  ( 59, "unused5"		), 
  ( 60, "endOper"		), 
  )

midicontrollers = (
  (1, "Mod Wheel"),
  (2, "Breath Contoller"),
  (4, "Foot Controller"),
  (5, "Portamento Time"),
  (7, "Main Volume"),
  (8, "Balance"),
  (10, "Pan"),
  (11, "Expression"),
  (12, "FX ctrl 1"),
  (13, "FX ctrl 2"),
  (16, "GP #1"),
  (17, "GP #2"),
  (18, "GP #3"),
  (19, "GP #4"),
  (64, "Sustain"),
  (65, "Portamento"),
  (66, "Sostenuto"),
  (67, "Soft Pedal"),
  (68, "Legato Footswitch"),
  (69, "Hold 2"),
  (70, "Sound C1 (Sound Variation)"),
  (71, "Sound C2 (Timbre/Harmonic Content)"),
  (72, "Sound C3 (Release Time)"),
  (73, "Sound C4 (Attack Time)"),
  (74, "Sound C5 (Brightness)"),
  (75, "Sound C6"),
  (76, "Sound C7"),
  (77, "Sound C8"),
  (78, "Sound C9"),
  (79, "Sound C10"),
  (80, "GP #5"),
  (80, "GP #6"),
  (80, "GP #7"),
  (80, "GP #8"),
  (84, "Portamento"),
  (91, "FX 1 Depth (External)"),
  (92, "FX 2 Depth (Tremolo)"),
  (93, "FX 3 Depth (Chorus)"),
  (94, "FX 4 Depth (Detune)"),
  (95, "FX 5 Depth (Phaser)"),
  )


MOD_VAL_MASK	= 0x007f
MOD_C_MASK	= 0x0080
MOD_D_MASK	= 0x0100
MOD_P_MASK	= 0x0200
MOD_TYPE_MASK	= 0xFC00


class SfMod(Uint16):

    def str(self, val):
	typev  = val & MOD_TYPE_MASK
	indexv = val & MOD_VAL_MASK
	type = modType.str(typev)
        if val & MOD_C_MASK:
	    C = "C"
	    index = midiCtrllr.str(indexv)
	else:
	    C = " "
	    index = generalCtrllr.str(indexv)
	if val & MOD_D_MASK:
	    D = "-"
	else:
	    D = "+"
	if val & MOD_P_MASK:
	    P = "P"
	else:
	    P = " "
	return "0x%04x: %s %s %s%s" % (val, type, P, D, index)

generalCtrllr	= Enum16(generalcontrollers)	# for a bit-field: don't use in structs
modType		= Enum16(modtypes)		# for a bit-field: don't use in structs

midiCtrllr	= Enum16(midicontrollers)
sampLink	= Enum16(samplinkvals)
sfGen		= Enum16(genvals)
sfTrans		= Enum16(modtranstypes)
sfMod		= SfMod()

chan_names = "LR3456"

def copy_samp_data(sfname, outf, chan):

    try:
	inf = file(sfname, "rb")
    except IOError, msg:
        print msg
	sys.exit(1)

    riff = jwave.RiffChunk(inf)
    riff.readHeader()
    iwave = jwave.WaveChunk(riff=riff, inf=inf)
    iwave.readHeader()

    if chan > iwave.fmt.numChan -1:
        print >>sys.stderr, (
	   "\nWarning: mono wave file '%s' for stereo soundfont"
	   % sfname)

    if iwave.fmt.bitsPerSample != 16:
        print "%s: Only 16-bit samples are supported by sf format" % sfname
	print "(bits per sample = %d)" % iwave.fmt.bitsPerSample
	sys.exit(1)

    if DEBUG:
        return 0

    iwave.seekSample(0)
    blksize = 4096

    if iwave.fmt.numChan == 1:
	sys.stdout.write(".")

	bytecount = iwave.numSamples * 2 # 2 bytes per sample
	# print "0x%08x, %9d" % (bytecount, iwave.numSamples)	# %%%

	count = bytecount
	while count > blksize:
	    outf.write(iwave.inf.read(blksize))
	    count -= blksize
	if count:
	    outf.write(iwave.inf.read(count))
    else:
	sys.stdout.write(chan_names[chan])
	bytecount = iwave.numSamples * 2 # 2 bytes per sample
	count = bytecount * iwave.fmt.numChan
	while count > blksize:
	    buf = iwave.inf.read(blksize)
	    for ix in range(0, blksize):
		if ((ix >> 1) % iwave.fmt.numChan) == chan:
		    outf.write(buf[ix])
	    count -= blksize
	if count:
	    buf = iwave.inf.read(count)
	    for ix in range(0, count):
		if ((ix >> 1) % iwave.fmt.numChan) == chan:
		    outf.write(buf[ix])

    return bytecount


def sample_info(sfname):
    try:
	inf = file(sfname, "rb")
    except IOError, msg:
        print msg
	sys.exit(1)

    riff = jwave.RiffChunk(inf)
    riff.readHeader()
    wave = jwave.WaveChunk(riff=riff, inf=inf)
    wave.readHeader()

    if wave.fmt.numChan == 1:
        stereo = False
    else:
        stereo = True

    if wave.fmt.bitsPerSample != 16:
        print "%s: Only 16-bit samples are supported by sf format" % sfname
	print "(bits per sample = %d)" % wave.fmt.bitsPerSample
	sys.exit(1)

    start_samp = 0
    num_samps = wave.numSamples
    rate = wave.fmt.sampleRate
    return (start_samp, num_samps, rate, stereo)

##########################################
#
# call handler for chunk if registered.
#
# args[0] = handlers
# args[1] = original args
#
def handle_sf_chunk(chunk, args):
    (handlers, callargs) = args
    if "*" in args[0]:
	(handler, harg) = handlers["*"]
	handler(chunk, (harg, callargs))
    if chunk.format in args[0]:
	(handler, harg) = handlers[chunk.format]
	handler(chunk, (harg, callargs))
    elif "?" in args[0]:
	(handler, harg) = handlers["?"]
	handler(chunk, (harg, callargs))

##########################################
#
class Sf:

    # NUM_ZEROS_AT_SAMPLE_END = 32
    # NUM_ZEROS_AT_SAMPLE_END = 46
    NUM_ZEROS_AT_SAMPLE_END = 100
    zeros = ""
    for ix in range(0, NUM_ZEROS_AT_SAMPLE_END):
        zeros += "\000\000"

    def __init__(self, inf=None, outf=None, stereo=False):
        self.riff = jriff.RiffFile(inf, outf)
	self.phdr = []
	self.pbag = []
	self.pmod = []
	self.pgen = []
	self.inst = []
	self.ibag = []
	self.imod = []
	self.igen = []
	self.shdr = []
	self.inf = inf
	self.outf = outf
	self.stereo = stereo

    def readRiff(self):
        self.riff.read()

    def walkriff(self, func, args=None):
        self.riff.walk(func, args)

    def handleriff(self, handlers, args=None):
        self.riff.walk(handle_sf_chunk, (handlers, self))

    def dumpriff(self, args=None):
        self.riff.walk(handle_sf_chunk, (_dumpriff, args))

    def readKmap(self, inf, basename):

	# set defaults

	self.bankname = basename
	self.presetname = basename	# %%% kluge: sf can have multiple
	self.samples = {}		# collect sample file names
	self.samplesByNum = []
	sampNdx = 0

	self.layers = []
	for line in inf.readlines():

	    line = line.strip()
	    if len(line) == 0 or line[0] == "#":
		continue

	    toks = line.split(":")
	    kw = toks[0]  
		
	    if kw == "BANKNAME":
		self.bankname = toks[1]
		print "bank name:", self.bankname

	    if kw == "DESIGNER":
		self.designer = toks[1]
		print "designer:", self.designer

	    if kw == "COPYRIGHT":
		self.copyright = toks[1]
		print "copyright:", self.copyright

	    if kw == "COMMENT":
		self.comment = toks[1]
		print "comment:", self.comment

	    if kw == "PRESET":
		self.presetname = toks[1]
		print "preset:", self.presetname

	    if kw == "RELEASE":
		rt = float(toks[1])
		self.release = int(1200.0 * math.log(rt, 2))

	    if kw == "VLAYER":
		vlname = toks[1]
		vl_lo  = toks[2]
		vl_hi  = toks[3]
		atten  = toks[4]
		vl_zones = []
		self.layers.append((vlname, int(vl_lo), int(vl_hi), int(atten), vl_zones))

	    if kw == "SAMP":
		fname	= toks[1]
		k_lo	= toks[2]
		k_hi	= toks[3]
		k_unity	= toks[4]
		vl_zones.append((fname, int(k_lo), int(k_hi)))
		if fname not in self.samples.keys():
		    self.samples[fname] = (fname, sampNdx)
		    self.samplesByNum.append((fname, int(k_unity)))
		    sampNdx += 1
		    if self.stereo:
			self.samplesByNum.append((fname, int(k_unity)))
			sampNdx += 1

	for l in self.layers:
	    (vlname, vl_lo, vl_hi, atten, vl_zones) = l
	    print "Layer:", vlname, "loV:", vl_lo, "hiV:", vl_hi, "atten(cB):", atten, len(vl_zones)

    def writeRiffHdr(self):
        self.outf.write("RIFF")
	self.riffLenLoc = self.outf.tell()
	self.outf.write("aaaa")	# write placeholder, come back later

	self.outf.write("sfbk")
	self.riffLen = 4	# count "sfbk" above

    def writeInfo(self):
        self.outf.write("LIST")
	len_loc = self.outf.tell()
	self.outf.write("aaaa")	# write placeholder, come back later

        self.outf.write("INFO")
	dlen = 4		# count "INFO" above

	self.outf.write("ifil")
	uint32.writeval(4, self.outf)
	dlen += 8
	dlen += uint16.writeval(2, self.outf)
	dlen += uint16.writeval(1, self.outf)

	PLAYER = "E-mu 10K1"

	self.outf.write("INAM")
	type = ChArray((jriff.roundup(len(self.bankname)+1),))
	uint32.writeval(type.size(), self.outf)
	dlen += 8
	dlen += type.writeval(self.bankname, self.outf)
	
	self.outf.write("isng")
	type = ChArray((jriff.roundup(len(PLAYER)+1),))
	uint32.writeval(type.size(), self.outf)
	dlen += 8
	dlen += type.writeval(PLAYER, self.outf)
	
	self.outf.write("IENG")
	type = ChArray((jriff.roundup(len(self.designer)+1),))
	uint32.writeval(type.size(), self.outf)
	dlen += 8
	dlen += type.writeval(self.designer, self.outf)
	
	TOOL="jMksf.py"
	self.outf.write("ISFT")
	type = ChArray((jriff.roundup(len(TOOL)+1),))
	uint32.writeval(type.size(), self.outf)
	dlen += 8
	dlen += jriff.roundup(type.writeval(TOOL, self.outf))

	self.outf.write("ICRD")
	y = time.localtime()
	tstamp = "%04d/%02d/%02d-%02d:%02d     " % (y[0], y[1], y[2], y[3], y[4])
	type = ChArray((jriff.roundup(len(tstamp)+1),))
	uint32.writeval(type.size(), self.outf)
	dlen += 8
	dlen += type.writeval(tstamp, self.outf)

	self.outf.write("ICMT")
	type = ChArray((jriff.roundup(len(self.comment)+1),))
	uint32.writeval(type.size(), self.outf)
	dlen += 8
	dlen += type.writeval(self.comment, self.outf)

	self.outf.write("ICOP")
	type = ChArray((jriff.roundup(len(self.copyright)+1),))
	uint32.writeval(type.size(), self.outf)
	dlen += 8
	dlen += type.writeval(self.copyright, self.outf)

	self.outf.seek(len_loc, 0)
	uint32.writeval(dlen, self.outf)
	self.outf.seek(len_loc + 4 + dlen, 0)

	return dlen + 8

    def writeSdta(self):
        self.outf.write("LIST")
	len_loc = self.outf.tell()
	self.outf.write("aaaa")	# write placeholder, come back later

        self.outf.write("sdta")
	dlen = 4		# count "sdata" above

	dlen += self.writeSmpl()

	self.outf.seek(len_loc, 0)
	uint32.writeval(dlen, self.outf)
	self.outf.seek(len_loc + 4 + dlen, 0)

	return dlen + 8

    def writeSmpl(self):
	self.outf.write("smpl")
	len_loc = self.outf.tell()
	self.outf.write("aaaa")	# write placeholder, come back later
	dlen = 0
	print "Copying sample data:", 

	if DEBUG:
	    print "(Test mode -- not actually copying sample data.)"

	ix = 0
        for (sfname, k_unity) in self.samplesByNum:
	    if self.stereo:
	        chan = ix & 1
	    else:
	        chan = 0
	    dlen += copy_samp_data(sfname, self.outf, chan)
	    self.outf.write(Sf.zeros)
	    dlen += Sf.NUM_ZEROS_AT_SAMPLE_END * 2
	    ix += 1
	print

	self.outf.seek(len_loc, 0)
	uint32.writeval(dlen, self.outf)
	self.outf.seek(len_loc + 4 + dlen, 0)

        return dlen + 8

    def writePhdr(self):
	name = "phdr"
	struc = _structs[name]
	self.outf.write(name)
	count = 1
	dlen = struc.size() * (count + 1)
	uint32.writeval(dlen, self.outf)

	# %%% Note: currently handles only one preset: should have a loop here,
	# and adjust the count above

	struc.writeval(
	    (
		self.presetname,	# presetName
		0,			# preset
		0,			# bank
		0,			# presetBagNdx
		0,			# library
		0,			# genre
		0,			# morphology
	    ), self.outf)

	struc.writeval(("EOP", 255,0,1, 0,0,0), self.outf)

	return dlen + 8


    def writePbag(self):
	name = "pbag"
	struc = _structs[name]
	self.outf.write(name)
	count = 1
	dlen = struc.size() * (count + 1)
	uint32.writeval(dlen, self.outf)

	genNdx = 0
	modNdx = 0
	struc.writeval((genNdx, modNdx), self.outf)
	genNdx += 1

	struc.writeval((genNdx, modNdx), self.outf)
        return dlen + 8

    def writePgen(self):
	name = "pgen"
	struc = _structs[name]
	self.outf.write(name)
	count = 1
	dlen = struc.size() * (count + 1)
	uint32.writeval(dlen, self.outf)

	instNdx = 0
	struc.writeval((
	    41,			# genOper: "instrument"
	    instNdx,		# genAmt: instrument index
	    ), self.outf)
	instNdx += 1

	struc.writeval((0, 0), self.outf)
        return dlen + 8

    def writePmod(self):
	name = "pmod"
	struc = _structs[name]
	self.outf.write(name)
	count = 0
	dlen = struc.size() * (count + 1)
	uint32.writeval(dlen, self.outf)

	struc.writeval((0, 0, 0, 0, 0), self.outf)

        return dlen + 8

    # One instrument; one ibag per zone
    # (Stereo: two ibags per zone?)

    def writeInst(self):
	name = "inst"
	struc = _structs[name]
	self.outf.write(name)
	count = 1
	dlen = struc.size() * (count + 1)
	uint32.writeval(dlen, self.outf)

	# Count the number of zones.
	self.num_zones = 0	# count & save number of zones, too
	for layer in self.layers:
	    (vlname, vl_lo, vl_hi, atten, vl_zones) = layer
	    for zone in vl_zones:
		self.num_zones += 1

	if self.stereo:
	    self.num_zones *= 2
	instBagNdx = 0
	struc.writeval((self.presetname, instBagNdx), self.outf)
	instBagNdx += self.num_zones

	struc.writeval(("EOI", instBagNdx), self.outf)
        return dlen + 8

    IGEN_PER_ZONE = 5

    def writeIbag(self):
	name = "ibag"
	struc = _structs[name]
	self.outf.write(name)
	len_loc = self.outf.tell()
	self.outf.write("aaaa")	# write placeholder, come back later
	igen_per_zone = Sf.IGEN_PER_ZONE
	if self.stereo:
	    igen_per_zone += 1

	genNdx = 0
	modNdx = 0
	for layer in self.layers:
	    (vlname, vl_lo, vl_hi, atten, vl_zones) = layer
	    for zone in vl_zones:
		struc.writeval((genNdx, modNdx), self.outf)
		genNdx += igen_per_zone
		if self.stereo:
		    struc.writeval((genNdx, modNdx), self.outf)
		    genNdx += igen_per_zone

	struc.writeval((genNdx, modNdx), self.outf)

	dlen = struc.size() * (self.num_zones + 1)
	self.outf.seek(len_loc, 0)
	uint32.writeval(dlen, self.outf)
	self.outf.seek(len_loc + 4 + dlen, 0)
        return dlen + 8

    def writeIgen(self):
	name = "igen"
	struc = _structs[name]
	self.outf.write(name)
	if self.stereo:
	    num_chans = 2
	    igen_per_zone = Sf.IGEN_PER_ZONE + 1
	else:
	    num_chans = 1
	    igen_per_zone = Sf.IGEN_PER_ZONE
	count = self.num_zones * igen_per_zone
	dlen = struc.size() * (count + 1)
	uint32.writeval(dlen, self.outf)

	if LOOP_FOR_SFZ:
	    # loop at the end to overcome sfz bug
	    # As it turns out, not necessary if there are extra zeros
	    looped = 1
	else:
	    looped = 0

	instNdx = 0
	for layer in self.layers:
	#{
	    (vlname, vl_lo, vl_hi, atten, vl_zones) = layer
	    for zone in vl_zones:
		(sname, k_lo, k_hi) = zone
		for ix in range(0, num_chans):
		    struc.writeval((
			43,			# genOper: "kRange"
			(k_hi << 8) + k_lo,	# genAmt: key range, lo-hi
			), self.outf)
		    struc.writeval((
			44,			# genOper: "vRange"
			(vl_hi << 8) + vl_lo,	# genAmt: velocity range, lo-hi
			), self.outf)
		    struc.writeval((
			38,			# genOper: "relVolEnv"
			self.release,		# genAmt: rel time
			), self.outf)
		    struc.writeval((
			54,			# genOper: "sModes"
			looped,			# genAmt: looped sample or not
			), self.outf)
		    if False:
			struc.writeval((
			    48,			# genOper: "initAtten"
			    atten,		# genAmt: 
			    ), self.outf)
		    if self.stereo:
		        if ix:
			    pan = 500
			else:
			    pan = -500
			struc.writeval((
			    17,				# genOper: "pan"
			    pan,			# genAmt: -500 for left, 500 for right.
			    ), self.outf)
		    struc.writeval((
			53,				# genOper: "sampID"
			self.samples[sname][1] + ix, 	# genAmt: sample index
			), self.outf)
	#}

	struc.writeval((0, 0), self.outf)
        return dlen + 8

    def writeImod(self):
	name = "imod"
	struc = _structs[name]
	self.outf.write(name)
	count = 0
	dlen = struc.size() * (count + 1)
	uint32.writeval(dlen, self.outf)

	struc.writeval((0, 0, 0, 0, 0), self.outf)

        return dlen + 8

    def writeShdr(self):
	name = "shdr"
	struc = _structs[name]
	self.outf.write(name)
	count = len(self.samplesByNum)
	dlen = struc.size() * (count + 1)
	uint32.writeval(dlen, self.outf)

	loc = 0
	ix = 0
        for (sfname, k_unity) in self.samplesByNum:
	    (start, count, rate, stereo) = sample_info(sfname)

	    sname = sfname.replace("\\", "/")
	    sname = sname.split("/")[-1].replace(".wav", "")
	    
	    if stereo :
	        if self.stereo:
		    if (ix & 1) == 0:
			modename = "left"
			mode = 4		# "leftSample"
			other = ix + 1
		    else:
			modename = "right"
			mode = 2		# "rightSample"
			other = ix - 1
			sname += "-r"
		else:
		    modename = "left"
		    mode = 1		# "monoSample"
		    other = 0
	    else:
		modename = "mono"
	        mode = 1		# "monoSample"
		other = 0

	    seconds = count / rate
	    msec = (count * 1000) / rate - seconds * 1000
	    print ( "%-24s %-6s, %3d:%03d sec"
		% (sfname, modename, seconds, msec))

	    if LOOP_FOR_SFZ:
		lstart = loc + count - 8
		lend   = loc + count
	    else:
	        lstart = 0
	        lend   = 0

	    struc.writeval(
		(
		    sname,
		    loc + start,
		    loc + count,
		    lstart,			# startLoop
		    lend,			# endLoop
		    rate,			# sampleRate
		    k_unity,			# origPitch
		    0,				# pitchCorrctn
		    other,			# sampleLink
		    mode,			# sampleType
		), self.outf)

	    loc += count + Sf.NUM_ZEROS_AT_SAMPLE_END
	    ix += 1

	struc.writeval(("EOS", 0,0,0,0,0,0,0,0,0), self.outf)

	return dlen + 8

    def writePdta(self):
        self.outf.write("LIST")
	len_loc = self.outf.tell()
	self.outf.write("aaaa")	# write placeholder, come back later

        self.outf.write("pdta")
	dlen = 4		# count "pdata" above

	dlen += self.writePhdr()
	dlen += self.writePbag()
	dlen += self.writePmod()
	dlen += self.writePgen()
	dlen += self.writeInst()
	dlen += self.writeIbag()
	dlen += self.writeImod()
	dlen += self.writeIgen()
	dlen += self.writeShdr()

	self.outf.seek(len_loc, 0)
	uint32.writeval(dlen, self.outf)
	self.outf.seek(len_loc + 4 + dlen, 0)

	return dlen + 8

    def writeFromKmap(self):
	self.writeRiffHdr()

        self.riffLen += self.writeInfo()
	self.riffLen += self.writeSdta()
	self.riffLen += self.writePdta()

	self.outf.seek(self.riffLenLoc, 0)
	uint32.writeval(self.riffLen, self.outf)

_chArray20 = ChArray((20,))
_structs = {}

_structs["phdr"] = Struct("phdr-entry", (
  ("presetName",	_chArray20	),
  ("preset",		uint16,		),
  ("bank",		uint16,		),
  ("presetBagNdx",	uint16,		),
  ("library",		uint32,		),
  ("genre",		uint32,		),
  ("morphology",	uint32,		),
  ))

_structs["pbag"] = Struct("pbag-entry", (
  ("genNdx",		uint16,		),
  ("modNdx",		uint16,		),
  ))


_structs["pmod"] = Struct("pmod-entry", (
  ("modSrcOper",	sfMod,		),
  ("modDstOper",	sfGen,		),
  ("modAmt",		uint16,		),
  ("modAmtSrcOper",	sfMod,		),
  ("modTransOper ",	sfTrans,	),
  ))

_structs["pgen"] = Struct("pgen-entry", (
  ("genOper",		sfGen,		),
  ("genAmt",		uint16,		),
  ))

_structs["inst"] = Struct("inst-entry", (
  ("instName",		_chArray20	),
  ("instBagNdx",	uint16,		),
  ))

_structs["ibag"] = Struct("ibag-entry", (
  ("instGenNdx",	uint16,		),
  ("instModNdx",	uint16,		),
  ))

_structs["imod"] = Struct("imod-entry", (
  ("modSrcOper",	sfMod,		),
  ("modDstOper",	sfGen,		),
  ("modAmt",		uint16,		),
  ("modAmtSrcOper",	sfMod,		),
  ("modTransOper ",	sfTrans,	),
  ))

_structs["igen"] = Struct("igen-entry", (
  ("genOper",		sfGen,		),
  ("genAmt",		uint16,		),
  ))

_structs["shdr"] = Struct("shdr-entry", (
  ("sampleName",	_chArray20	),
  ("start",		uint32,		),
  ("end",		uint32,		),
  ("startLoop",		uint32,		),
  ("endLoop",		uint32,		),
  ("sampleRate",	uint32,		),
  ("origPitch",		uint8,		),
  ("pitchCorrctn",	sint8,		),
  ("sampleLink",	uint16,		),
  ("sampleType",	sampLink,	),
  ))

def indent_print(str, level):
    print "%*s%s" % (level*2, "", str)

def dump_typeval(name, type, val, args, level):

    if args:
	indent_print("%-20s: %s" % (name, type.str(val) + args), level)
	return

    indent_print("%-20s: %s" % (name, type.str(val)), level)

def dump_typevalloc(name, type, val, args, level):

    (chunk, offset) = args
    loc = chunk.inf_loc + offset
    print "0x%08x  %*s%-20s: %s" % (loc, level*2, "", name, type.str(val))


def read_chunkstructs(chunk, args):

    (hargs, sf) = args
    if chunk.format not in _structs:
	dumpr_chunk(chunk, hargs)
	return

    attr = getattr(sf, chunk.format, None)
    if attr == None:
	chunk.prn(chunk.format)
	return

    chunk.iseek()
    struc = _structs[chunk.format]
    slen = struc.Len
    loc = 0
    while loc < chunk.len:
	val = struc.read(chunk.inf())
	var = struc.var(val)
	var.structify()
	attr.append((var, chunk))

	loc += slen

def dumpr_chunkstructs(chunk, args):

    (hargs, callargs) = args
    if chunk.format not in _structs:
	dumpr_chunk(chunk, hargs)
	return

    chunk.prnLoc(chunk.format)

    chunk.iseek()
    struc = _structs[chunk.format]
    slen = struc.Len
    offset = 0
    while offset < chunk.len:
	# chunk.prn(" LOC = 0x%08x" % offset)
	val = struc.read(chunk.inf())
	struc.walkval(val, dump_typevalloc, (chunk, offset), 2)
	offset += slen

# Handlers:
#
#  Each handler is a map of (func, arg) pairs.
#
#  Register for chunk name
#  Register "*" to be called for all
#  Register "?" to be called if no specific handler is registered
#
#  Register function of the form func(chunk, args)
#  Return value ignored

def dumpr_chunk(chunk, args=None):
    chunk.printHdr()

def do_ifil(chunk, args):
    (hargs, callargs) = args
    chunk.iseek()
    major = jriff.get_uint16(chunk.inf())
    minor = jriff.get_uint16(chunk.inf())

    if hargs:
	chunk.prn("SF Spec Version: %d.%d" % (major, minor))


# read & dump string-20 chunk

def do_string(chunk, args):

    (hargs, callargs) = args
    (desc, inchunk) = hargs
    chunk.iseek()
    name = chunk.inf().read(chunk.len)
    ix = name.find("\000")
    if ix != -1:
        name = name[0:ix]
    if inchunk:
	chunk.prn("%s: %s" % (desc, name))
    else:
	print "%s: %s" % (desc, name)


_read = {}
_dumpriff = {}

_dumpriff["?"]		= ( dumpr_chunk,	None)
_dumpriff["ifil"]	= ( do_ifil,		True)
_dumpriff["INAM"]	= ( do_string,		("BankName",	True))
_dumpriff["isng"]	= ( do_string,		("Engine",	True))
_dumpriff["irom"]	= ( do_string,		("Rom",		True))
_dumpriff["ICRD"]	= ( do_string,		("Created",	True))
_dumpriff["IENG"]	= ( do_string,		("Designer",	True))
_dumpriff["IPRD"]	= ( do_string,		("Product",	True))
_dumpriff["ICOP"]	= ( do_string,		("Copyright",	True))
_dumpriff["ICMT"]	= ( do_string,		("Comment",	True))
_dumpriff["ISFT"]	= ( do_string,		("Tools",	True))

_dumpriff["phdr"]	= ( dumpr_chunkstructs, True)
_dumpriff["pbag"]	= ( dumpr_chunkstructs, True)
_dumpriff["pmod"]	= ( dumpr_chunkstructs, True)
_dumpriff["pgen"]	= ( dumpr_chunkstructs, True)
_dumpriff["inst"]	= ( dumpr_chunkstructs, True)
_dumpriff["ibag"]	= ( dumpr_chunkstructs, True)
_dumpriff["imod"]	= ( dumpr_chunkstructs, True)
_dumpriff["igen"]	= ( dumpr_chunkstructs, True)
_dumpriff["shdr"]	= ( dumpr_chunkstructs, True)

# _read["?"]	= ( do_chunk,	False)
_read["ifil"]	= ( do_ifil,	False)
_read["INAM"]	= ( do_string,	("Bank Name",	False))
_read["isng"]	= ( do_string,	("Engine",	False))
_read["irom"]	= ( do_string,	("Rom",		False))
_read["ICRD"]	= ( do_string,	("Created",	False))
_read["IENG"]	= ( do_string,	("Designer",	False))
_read["IPRD"]	= ( do_string,	("Product",	False))
_read["ICOP"]	= ( do_string,	("Copyright",	False))
_read["ICMT"]	= ( do_string,	("Comment",	False))
_read["ISFT"]	= ( do_string,	("Tools",	False))

_read["phdr"]	= ( read_chunkstructs, None)
_read["pbag"]	= ( read_chunkstructs, None)
_read["pmod"]	= ( read_chunkstructs, None)
_read["pgen"]	= ( read_chunkstructs, None)
_read["inst"]	= ( read_chunkstructs, None)
_read["ibag"]	= ( read_chunkstructs, None)
_read["imod"]	= ( read_chunkstructs, None)
_read["igen"]	= ( read_chunkstructs, None)
_read["shdr"]	= ( read_chunkstructs, None)


# dump SF when all we've done so far is sf.riffRead

def dumpriff(cmd, args):
    if len(args) < 1:
	usage(cmd)
	sys.exit(1)

    infname = args[0]
    del args[0]

    if not infname.endswith(".sf2"):
        infname += ".sf2"

    try:
	inf  = file(infname, "rb")
    except IOError, msg:
        print msg
	sys.exit(1)

    sf = Sf(inf)
    sf.readRiff()
    sf.dumpriff()

_important_igen_opers = (
  "kRange",
  "vRange",
  # "initFFc",
  # "relVolEnv",
  "sampID",
  )

labeled = False

def dumpSampID(sf, sampId, level):
    if sampId >= len(sf.shdr):
	indent_print("*** MISSING SHDR ***", level)
	return
    (sampv, sampch) = sf.shdr[sampId]
    sampv.walk(dump_typeval, args, level, "0x%04x" % sampId)


def dump(cmd, args):
    global labeled

    if len(args) < 1:
        usage(cmd)
	sys.exit(1)

    infname = args[0]
    del args[0]

    if not infname.endswith(".sf2"):
        infname += ".sf2"

    try:
	inf  = file(infname, "rb")
    except IOError, msg:
        print msg
	sys.exit(1)

    sf = Sf(inf)
    sf.readRiff()
    sf.handleriff(_read)

    # dump each preset

    print
    print "Presets"

    phdr_ix = 0
    for (phdrv, phdrch) in sf.phdr:
    #{
	if phdrv.preset == 255:
	    break

	# dump the preset header
	phdrv.walk(dump_typeval, None, 1, "0x%04x" % phdr_ix)

	# find the index range of pbag entries for this preset

	(next_phdrv, next_phdrch) = sf.phdr[phdr_ix+1]
	pbag_ix_end = next_phdrv.presetBagNdx
	pbag_ix =          phdrv.presetBagNdx

	# dump the pbag entries

	for (pbagv, pbagch) in sf.pbag[pbag_ix:pbag_ix_end]:
	#{
	    # dump the pbag block -- not that it says much!
	    pbagv.walk(dump_typeval, None, 2, "0x%04x" % pbag_ix)

	    # find the index range of preset generators for this pbag entry

	    (next_pbagv, next_pbagch) = sf.pbag[pbag_ix+1]
	    pgen_ix_end = next_pbagv.genNdx
	    pgen_ix =          pbagv.genNdx

	    # dump the preset generators

	    for (pgenv, pgench) in sf.pgen[pgen_ix:pgen_ix_end]:
	    #{
		pgenv.walk(dump_typeval, None, 3, "0x%04x" % pgen_ix)

		# if it's an instrument
		if pgenv.genOper == "instrument":
		#{
		    print "                 Inst", pgenv.genAmt
		    
		#} if inst end

		pgen_ix += 1
	    #} pgen loop end

	    # %%% find the index range of preset modulators for this pbag entry
	    # %%% dump the preset modulators

	    pbag_ix += 1
	#} pbag loop end

	phdr_ix += 1
    #} phdr loop end

    # Dump the instruments

    print
    print "Instruments"
    for inst_ix in range(0, len(sf.inst)-1):
    #{

	# get and dump its inst entry
	(instv, instch) = sf.inst[inst_ix]
	instv.walk(dump_typeval, None, 1, "0x%04x" % inst_ix)

	# get the index range for the inst entry's ibags
	(next_instv, next_instch) = sf.inst[inst_ix+1]
	ibag_ix_end = next_instv.instBagNdx
	ibag_ix =          instv.instBagNdx

	# dump its ibags
	for (ibagv, ibagch) in sf.ibag[ibag_ix:ibag_ix_end]:
	#{
	    ibagv.walk(dump_typeval, None, 2, "0x%04x" % ibag_ix)

	    # contains igen, imod

	    # get the index range for the ibag's igens
	    if len(sf.ibag) <= ibag_ix + 1:
		indent_print("*** MISSING IBAG? ***", 2)
		break;
	    (next_ibagv, next_ibagch) = sf.ibag[ibag_ix+1]
	    igen_ix_end = next_ibagv.instGenNdx
	    igen_ix =          ibagv.instGenNdx

	    # dump the igens
	    for (igenv, igench) in sf.igen[igen_ix:igen_ix_end]:
	    #{
		igenv.walk(dump_typeval, None, 3, "0x%04x" % igen_ix)
		igen_ix += 1
	    #} igen loop end
	    print

	    # dump the imods

	    # get the index range for the ibag's imods
	    imod_ix_end = next_ibagv.instModNdx
	    imod_ix =          ibagv.instModNdx

	    # dump the imods
	    for (imodv, imodch) in sf.imod[imod_ix:imod_ix_end]:
	    #{
		imodv.walk(dump_typeval, None, 4, "0x%04x" % imod_ix)
		imod_ix += 1
	    #} imod loop end

	    ibag_ix += 1
	#} ibag loop end

    #}

    # dump the samples
    print
    print "Sample Headers"
    for samp_ix in range(0, len(sf.shdr)-1):
     	dumpSampID(sf, samp_ix, 1)


def build(cmd, args, stereo=False):

    if len(args) < 1:
	usage(cmd)
	sys.exit(1)

    infname = args[0]
    del args[0]

    if not infname.endswith(".sfk"):
        infname += ".sfk"

    try:
	inf  = file(infname, "r")
    except IOError, msg:
        print msg
	sys.exit(1)

    print "Input file: ", infname

    inf_basename = ".".join(infname.split(".")[0:-1])

    if len(args) > 0:
        outfname = args[0]
	del args[0]
	if not outfname.endswith(".sf2"):
	    outfname += ".sf2"
    else:
	# use infname, replacing ext with .sf2
	outfname = inf_basename + ".sf2"
	
    try:
	outf = file(outfname, "wb")
    except IOError, msg:
        print msg
	sys.exit(1)

    print "Output file:", outfname

    sf = Sf(outf=outf, stereo=stereo)
    sf.readKmap(inf, inf_basename)
    sf.writeFromKmap()


def usage(cmd):
    print >>sys.stderr
    print >>sys.stderr, "%s: Jeff's soundfont builder/dumper" % cmd
    print >>sys.stderr
    print >>sys.stderr, "usage:"
    print >>sys.stderr, "  %s [-s] [-t] <mapfile> [<sffile>] -- build soundfont from samples and keymap file" % cmd
    print >>sys.stderr, "  %s -d <sffile>                    -- dump soundfont's presets hierarchically" % cmd
    print >>sys.stderr, "  %s -r <sffile>                    -- dump soundfont riff structure" % cmd
    print >>sys.stderr
    print >>sys.stderr, "  -s = stereo soundfont -- all samples must be stereo"
    print >>sys.stderr, "  -t = test mode: don't copy samples"
    print >>sys.stderr, "  <mapfile> = keymap (.sfk) file, as produced by jMap.py."
    print >>sys.stderr, "  <sffile>  = soundfont (.sf2) file."
    print >>sys.stderr
    print >>sys.stderr, "  Omit extensions for .sf2 and .sfk files (appended by program)"
    print >>sys.stderr
    sys.exit(1)

# Main

if __name__ == "__main__":

    stereo = False

    args = sys.argv
    cmd = args[0].split("\\")[-1]
    del args[0]

    if len(args) >= 1 and args[0] == "-s":
        stereo=True
	del args[0]

    if len(args) >= 1 and args[0] == "-t":
        DEBUG=True
	del args[0]

    if len(args) < 1 or args[0] == "-?": 
        usage(cmd)
	sys.exit(1)

    if args[0] == "-d": 
	del args[0]
        dump(cmd, args)
	sys.exit(0)

    if args[0] == "-r": 
	del args[0]
        dumpriff(cmd, args)
	sys.exit(0)

    build(cmd, args, stereo=stereo)
