# Build keyboard map for samples
#
# Builds soundfont key map given a set of sample files
# and a little config data.
#
# Sample files must be named according to a convention:
#
#  xxxx_<mnote>_xxxx_<layer>.wav
#
#  where
#    <mnote> is the MIDI note number
#    <layer> is arbitrary text identifying the layer (see layer config below)
#
# UPDATE:
#   Set VEL_LOC and NOTE_LOC to specify format

import sys
import warnings
import glob

import jmidi
import jtime
import jtrans

# index constants

LNAME	= 0
LVEL	= 1
LATTEN	= 2

# initializations 

LAYER = []

############################################################################
#
# Configuration (should be read in)
#

# How to find layer name and note from file name:

# DELIMS are the characters treated as delimiters to split the
# file name.
# After splitting a line into parts separated by the delimiter,
# LOC is the location of the note or layer name, where 0 is the
# first part, 1 is the second, etc.  -1 is the last, -2 is the
# second to last, etc.

DELIMS		= " `~!@#$%^&*()_+-={}|[]:\";'<>?,.\t"
LAYER_LOC	= -1

NOTE_LOC	= -2

# Soundfont header items

BANKNAME	= "jrsp73b"
DESIGNER	= "Scarbee"
COPYRIGHT	= "2003, Scarbee"
COMMENT		= ""

# Preset definitions.  Currently, only one preset supported.

PRESETNAME	= BANKNAME

RELEASE		= 0

# Velocity layers for preset. 
# Names are arbitrary, but must be listed softest to loudest

#             name   MIDI velocity	atenuation (dB x 10)
# LAYER.append(("s3",	 17,		220))
# LAYER.append(("s1",	 37,		180))
# LAYER.append(("ms2",	 57,		140))
# LAYER.append(("m3",	 77,		100))
# LAYER.append(("m1",	 97,		 60))
# LAYER.append(("h2",	117,		 20))

# mapping parameters

MAX_LAYER_SHIFT		= 2		# don't jump layers more than this
MAX_NOTE_SHIFT		= 7		# don't stretch pitch more than this

NOTE_SHIFT_COST		= 2		# relative cost of shifing notes (vs. layers)
LAYER_SHIFT_COST	= 1		# relative cost of shifing layers (vs. notes)

EXTEND_LAYER_UP	= True		# whether better to map higher vel  sample than lower
EXTEND_NOTE_UP	= True		# whether better to map higher note sample than lower

# desired range for whole keyboard map

LO_KEY		= jmidi.notenum("C1")	# lowest C on piano, lowest key I use
HI_KEY		= jmidi.notenum("G7")	# highest key on MR76

###############################################################################

class Globals:
    def __init__(self):
        pass

gl = Globals
gl.grid = []
gl.samps = {}
gl.layernum = {}
gl.lnamelen = 0

class Samp:
    def __init__(self):
        pass

def build_grid(grid):

    for layer in range(0, len(LAYER)):
	grid.append([])
        for key in range(0, HI_KEY+MAX_NOTE_SHIFT+1):
	    grid[layer].append(None)

	gl.layernum[LAYER[layer][LNAME]] = layer

def build_sampchars():

    # omit ANSI and DOS unprintables (7f only one for DOS)
    # unprintables = [0x7f, 0x81, 0x8d, 0x8f, 0x90, 0x9d,]

    chars = ""

    # for ichar in range(ord('"'), 0xff): 
    for ichar in range(ord('"'), 0x7f): 
	# if ichar not in unprintables:
	    chars += chr(ichar)

    return chars


def load_filenames(args):
    global gl

    warnings = []
    errors = []

    for arg in args: 
    #{
	for sampfname in glob.glob(arg):

	    if True:
		try:
		    sampf = file(sampfname, "rb")
		except IOError, msg:
		    errors.append(msg)

		if sampf:
		    sampf.close()

	    samp = Samp()

	    # strip directory
	    basename = sampfname.replace("\\", "/")
	    basename = sampfname.split("/")[-1]

	    # strip ".wav" extension
	    basename = basename.split(".")
	    basename = ".".join(basename[0:-1])
	    basename = jtrans.tr(basename, DELIMS, " ")

	    # get layer name

	    parts = basename.split(" ")
	    if len(parts) <= abs(LAYER_LOC):
	        loc = LAYER_LOC
		if loc >= 0:
		    loc += 1
	        print >>sys.stderr, (
		    "After splitting filename '%s' delimiters,"
		    % (basename))
	        print >>sys.stderr, (
		    "there aren't enough parts to find part number %d." % loc)
		sys.exit(1)
	    layername  = parts[LAYER_LOC]

	    # get note: might be MIDI number or note name

	    if len(parts) <= abs(NOTE_LOC):
	        loc = NOTE_LOC
		if loc >= 0:
		    loc += 1
	        print >>sys.stderr, (
		    "After splitting filename '%s' at delimiters, there aren't"
		    % (basename))
	        print >>sys.stderr, (
		    "there aren't enough parts to find part number %d." % loc)
		sys.exit(1)
	    notespec   = parts[NOTE_LOC]

	    mnote = jmidi.notenum(notespec)
	    if mnote == None:
	        print >>sys.stderr, (
		    "Invalid MIDI note designation '%s' in '%s'"
		    % (notespec, basename))
		sys.exit(1)

	    # print sampfname, mnote, layername, jmidi.mnote_name(mnote)[0]
	    samp.fname = sampfname
	    samp.mnote = mnote
	    samp.notename = jmidi.mnote_name(mnote, pad=None)
	    samp.layername = layername
	    if layername not in gl.layernum:
	        warnings.append("Sample for unconfigured layer '%s': %s"
		    % (samp.layername, samp.fname))
		continue
	    samp.layer = gl.layernum[layername]

	    if samp.layer == None:
	        warnings.append("Sample for missing layer '%s': %s"
		    % (samp.layername, samp.fname))
		continue

	    x = LO_KEY - MAX_NOTE_SHIFT
	    if (samp.mnote < max(0, LO_KEY - MAX_NOTE_SHIFT)
		or samp.mnote > HI_KEY + MAX_NOTE_SHIFT):

		warnings.append("Sample outside useful note range (%s): %s" 
		    % (samp.notename, samp.fname))
		continue

	    samp.char = None
	    gl.samps[sampfname] = samp
	    gl.grid[samp.layer][mnote] = samp

    #}

    if errors:
        for msg in errors:
            print >>sys.stderr, msg
        sys.exit(1)

    if warnings:
        for msg in warnings:
            print >>sys.stderr, "Warning:", msg

    # print the samples, along with a character to assigned for
    # showing the key map in showmap().

    print >>gl.ofile, "# Samples:"

    sampnum = 0
    sampchars = build_sampchars()

    for layer in range(len(LAYER)-1, -1, -1):
	print >>gl.ofile, (
	    "#   Layer %*s vel %3d: "
	    % (gl.lnamelen, LAYER[layer][LNAME], LAYER[layer][LVEL])),
        for mnote in range(LO_KEY, HI_KEY+1):
	    samp = gl.grid[layer][mnote]
	    if samp:
		if samp.char == None:
		    samp.char = sampchars[sampnum]
		    sampnum += 1
		    if sampnum >= len(sampchars):
			sampnum = 0
	        print >>gl.ofile, "%3s=%c" % (samp.notename, samp.char),
	    
	print >>gl.ofile

    print >>gl.ofile

def window(row, col, bounds):
    row_min = bounds[0]
    row_max = bounds[1]
    col_min = bounds[2]
    col_max = bounds[3]

    row_lo = max(row - MAX_LAYER_SHIFT, row_min)
    row_hi = min(row + MAX_LAYER_SHIFT, row_max)
    col_lo = max(col - MAX_NOTE_SHIFT, col_min)
    col_hi = min(col + MAX_NOTE_SHIFT, col_max)

    return (row_lo, row_hi, col_lo, col_hi)


def distance(torow, tocol, fromrow, fromcol):
    row_dist = (abs(torow - fromrow) * LAYER_SHIFT_COST) * 2
    col_dist = (abs(tocol - fromcol) * NOTE_SHIFT_COST) * 2

    if torow > fromrow and EXTEND_LAYER_UP:
        row_dist += 1
    elif torow < fromrow and not EXTEND_LAYER_UP:
        row_dist += 1
   
    if tocol > fromcol and EXTEND_NOTE_UP:
        col_dist += 1
    elif tocol < fromcol and not EXTEND_NOTE_UP:
        col_dist += 1

    # print "(", fromrow, fromcol, ")",
    # print torow, fromrow, "=>", row_dist, "|", tocol, fromcol, "=>", col_dist
    return col_dist + row_dist

def sname(samp):
    return "%s-%s" % (samp.layername, samp.notename)

def assign_keys(map):
    global gl

    # fix bounds of search
    row_min = 0
    row_max = len(LAYER)-1
    col_min = LO_KEY
    col_max = HI_KEY

    bounds = (row_min, row_max, col_min - MAX_NOTE_SHIFT, col_max + MAX_NOTE_SHIFT)
    keymap = []
    build_grid(keymap)


    for row in range(row_min, row_max+1):
    #{
	# set initial window for this row pass
	win = window(row, col_min, bounds)

	# load initial neighbors.  Omit rightmost column (they're added below)

	neighbors = []	# (samp, row, col)

	col = 0
	for rr in range(win[0], win[1]+1):
	    for cc in range(win[2], win[3]):
		nbr = gl.grid[rr][cc]
		if nbr:
		    # print "init:", sname(nbr)
		    neighbors.append((nbr, rr, cc))

        for col in range(col_min, col_max+1):
	#{

	    # set new window
	    win = window(row, col, bounds)

	    # add new neighbors at right of window
	    cc = win[3]
	    for rr in range(win[0], win[1]+1):
	        nbr = gl.grid[rr][cc]
		if nbr:
		    # print "new: ", rr, cc, sname(nbr)
		    neighbors.append((nbr, rr, cc))

	    # Visit neighbors.
	    # Discard any neighbors in old left column.
	    # Go backwards to make deletion easy
	    # Calculate distance and find closest neighbor.

	    bestdist = 9999
	    bestnbr = None

	    # print jmidi.mnote_name(col), len(neighbors), col, win
	    if len(neighbors) == 0:
	        ### print >>sys.stderr, " -- No neighbors for layer", row, "key", col
		pass
	    for nbrix in range(len(neighbors)-1, -1, -1):
	        (nbr, rr, cc) = neighbors[nbrix]
		if cc < win[2]:
		    del neighbors[nbrix]
		    continue
		
		dist = distance(rr, cc, row, col)
		# print "  ", row, col, rr, cc, ":", dist,
		if dist < bestdist:
		    bestnbr = nbr
		    bestdist = dist

	    keymap[row][col] = bestnbr
	#}
    #}

    gl.grid = keymap



def showmap(grid, layerdata):

    # Generate heading showing "piano keyboard" in three lines:
    # first line is octave number
    # second line is key name, omitting sharp or flat
    # third line is "b" for flats and " " for naturals
    #
    # Example:
    #    111111111111222222222222333333333333444444444444...
    #    CDDEEFGGAABBCDDEEFGGAABBCDDEEFGGAABBCDDEEFGGAABB...
    #     b b  b b b  b b  b b b  b b  b b b  b b  b b b ... 

    line1 = line2 = line3 = ""
    for col in range(LO_KEY, HI_KEY+1):
        notename = jmidi.mnote_name(col, pad=None)
	line2 += notename[0]
	if notename[1] == "b":
	    line3 += "b"
	    octave = notename[2]
	else:
	    line3 += " "
	    octave = notename[1]
	line1 += octave

    # print "keyboard"
    print >>gl.ofile, "#", line1
    print >>gl.ofile, "#", line2
    print >>gl.ofile, "#", line3
    print >>gl.ofile, "#"

    # print key assignments

    for row in range(len(layerdata)-1, -1, -1):
	line = ""
    	for col in range(LO_KEY, HI_KEY+1):
	    samp = gl.grid[row][col]
	    if samp:
		if samp.layer == row and samp.mnote == col:
		    line += " "
		else:
		    line += samp.char
	    else:
		line += "!"
	print >>gl.ofile, (
	    "# %s Layer %-6s v=%03d"
	    % (line, layerdata[row][LNAME], layerdata[row][LVEL]))

    print >>gl.ofile, "#"
    print >>gl.ofile, "#  Key:"
    print >>gl.ofile, "#    space = unity-mapped key"
    print >>gl.ofile, "#    !     = unmapped key"
    print >>gl.ofile, "#    anything else: see sample layer list above"


def emit_keymap(samp, keyLo, keyHi):
    print >>gl.ofile, "  SAMP:%s:%d:%d:%d:\t(%3s - %3s)" % (
        samp.fname, keyLo, keyHi, samp.mnote,
	jmidi.mnote_name(keyLo, None),
	jmidi.mnote_name(keyHi, None))

def emit_map(grid, layerdata):

    print >>gl.ofile
    print >>gl.ofile, "BANKNAME:%s" % BANKNAME
    print >>gl.ofile, "DESIGNER:%s" % DESIGNER
    print >>gl.ofile, "COPYRIGHT:%s" % COPYRIGHT
    print >>gl.ofile, "COMMENT:%s" % COMMENT

    print >>gl.ofile
    print >>gl.ofile, "PRESET:%s" % PRESETNAME
    print >>gl.ofile
    print >>gl.ofile, "RELEASE:%s" % RELEASE

    lastVel = 0
    for row in range(0, len(layerdata)):
    #{
	curVel = layerdata[row][LVEL]
	atten  = layerdata[row][LATTEN]

	print >>gl.ofile
        print >>gl.ofile, "VLAYER:%s:%3d:%3d:%2d" % (
	    layerdata[row][LNAME], lastVel + 1, curVel, atten)

	lastSamp = None

    	for col in range(LO_KEY, HI_KEY+1):
	#{
	    samp = gl.grid[row][col]
	    if samp != lastSamp:
	        if lastSamp != None:
                    emit_keymap(lastSamp, firstKey, col-1)
		lastSamp = samp
		firstKey = col
	#}

	# handle last unfinished keymap
	if lastSamp != None:
	    emit_keymap(lastSamp, firstKey, col)

        lastVel = curVel
    #}


def convert_int(val, lineno):
    try:
        ival = int(val)
    except:
        print >>sys.stderr, (
	    "Line %d: expecting integer, got '%s'"
	    % (lineno, val))
	sys.exit(1)
    return (ival)

def kwval(group, lineno):

    try:
        (kw, val) = group.split("=")
    except Exception, msg:
        print >>sys.stderr, (
	    "Line %d: expecting 'keyword=value' format, got '%s'"
	    % (lineno, group))
        print >>sys.stderr, msg
	raise Exception
	sys.exit(1)
    return (kw, val)

def process_cfg(cfg_fname):
#{
    global LAYER_LOC, NOTE_LOC
    global BANKNAME, DESIGNER, COPYRIGHT, COMMENT
    global LO_KEY, HI_KEY
    global MAX_LAYER_SHIFT, LAYER_SHIFT_COST, EXTEND_LAYER_UP
    global MAX_NOTE_SHIFT, NOTE_SHIFT_COST, EXTEND_NOTE_UP
    global PRESETNAME, RELEASE, LAYER
    global gl

    try:
	cfgf = file(cfg_fname, "r")
    except Exception, msg:
	print >>sys.stderr, msg
	sys.exit(1)

    COMMENT = ""
    layers = []
    lvmode = None

    lineno = 0
    for iline in cfgf.readlines():
    #{
        line = jtrans.tr(iline.strip(), "\t", " ")
	lineno += 1

	# skip blank line or comment
	if len(line) == 0 or line[0] == "#":
	    continue

        # print >>sys.stderr, line 

	groups = line.split(" ")
	cmd = groups[0]
	for ix in range(len(groups)-1, -1, -1):
	    if len(groups[ix]) == 0:
	        del groups[ix]

	if cmd == "bankname":
	    BANKNAME = " ".join(groups[1:])
	    PRESETNAME = BANKNAME	# default

	if cmd == "designer":
	    DESIGNER = " ".join(groups[1:])

	if cmd == "copyright":
	    COPYRIGHT = " ".join(groups[1:])

	if cmd == "comment":
	    COMMENT += " ".join(groups[1:])

	if cmd == "preset":
	    if len(groups) >= 2:
		PRESETNAME = " ".join(groups[1:])

        if cmd == "release":
	    if len(groups) < 2:
	        print >>sys.stderr, (
		    "Line %d: expecting release value."
		    % (lineno))
		sys.exit(1)
	    val = groups[1]
	    try:
		RELEASE = float(val)
	    except:
	        print >>sys.stderr, (
		    "Line %d: expecting float value for release time, got '%s'."
		    % (lineno, val))
		sys.exit(1)

	if cmd == "layer-opts":
	    for group in groups[1:]:
	        if len(group) == 0:
		    continue

		(kw, val) = kwval(group, lineno)

		if kw == "max-shift":
		    MAX_LAYER_SHIFT = convert_int(val, lineno)

		elif kw == "shift-cost":
		    LAYER_SHIFT_COST = convert_int(val, lineno)

		elif kw == "extend-up":
		    if val.upper() == "Y":
			EXTEND_LAYER_UP = True
		    else:
			EXTEND_LAYER_UP = False
	if cmd == "note-opts":
	    for group in groups[1:]:
	        if len(group) == 0:
		    continue

		(kw, val) = kwval(group, lineno)

		if kw == "max-shift":
		    MAX_NOTE_SHIFT = convert_int(val, lineno)

		elif kw == "shift-cost":
		    NOTE_SHIFT_COST = convert_int(val, lineno)

		elif kw == "extend-up":
		    if val.upper() == "Y":
			EXTEND_NOTE_UP = True
		    else:
			EXTEND_NOTE_UP = False


	if cmd == "keyboard-range":
	    for group in groups[1:]:
	        if len(group) == 0:
		    continue

		(kw, val) = kwval(group, lineno)

		if kw == "low-key":
		    key = jmidi.notenum(val)
		    if key == None:
		        print >>sys.stderr, (
			    "Line %d: expecting note name, got '%s'."
			    % (lineno, val))
			sys.exit(1)
		    LO_KEY = key
		    # print >>sys.stderr, "LO_KEY", key

		elif kw == "high-key":
		    key = jmidi.notenum(val)
		    if key == None:
		        print >>sys.stderr, (
			    "Line %d: expecting note name, got '%s'."
			    % (lineno, val))
			sys.exit(1)
		    HI_KEY = key

	# sample filename format (the parts we need to know)

	if cmd == "format":
	    for group in groups[1:]:

		(kw, val) = kwval(group, lineno)

		if kw == "layer-loc":
		    ival = convert_int(val, lineno)
		    if ival > 0:
		        ival -= 1
		    LAYER_LOC = ival

		elif kw == "note-loc":
		    ival = convert_int(val, lineno)
		    if ival > 0:
		        ival -= 1
		    NOTE_LOC = ival

	if cmd == "layer":
	    if len(groups) < 2:
		print >>sys.stderr, (
		    "Line %d: expecting layer name."
		    % (lineno))
		sys.exit(1)

	    lname	= groups[1]
	    latten	= 0
	    lvel	= -1
	    lrange	= -1

	    gl.lnamelen = max(gl.lnamelen, len(lname))

	    for group in groups[2:]:
	        if len(group) == 0:
		    continue

		(kw, val) = kwval(group, lineno)

		if kw == "vel":
		    if lvmode and lvmode != "vel":
			print >>sys.stderr, (
			    "Line %d: can't mix 'vel' and 'vel-range' in same preset."
			    % (lineno))
			sys.exit(1)
		    lvel = convert_int(val, lineno)
		    lvmode = "vel"

		elif kw == "vel-range":
		    if lvmode and lvmode != "range":
			print >>sys.stderr, (
			    "Line %d: can't mix 'vel' and 'vel-range' in same preset."
			    % (lineno))
			sys.exit(1)
		    lrange = convert_int(val, lineno)
		    lvmode = "range"

		elif kw == "atten":
		    latten = convert_int(val, lineno)

	    layers.append((lname, lvel, lrange, latten))

    #}

    # Are we assigning velocities?

    if lvmode == "vel":

        # No.  Check the assignments.
	last_lvel = -1
	for (lname, lvel, lrange, latten) in layers:
	    if lvel == -1:
		print >>sys.stderr, (
		    "No velocity assigned for layer '%s'" 
		    % lname)
		sys.exit(1)
	    if lvel <= last_lvel:
		print >>sys.stderr, (
		    "Velocity for layer '%s' must be higher than previous layer" 
		    % lname)
		sys.exit(1)
	    last_lvel = lvel

	if last_lvel != 127:
	    print >>sys.stderr, (
		"Warning: velocity for top layer '%s' should be 127" 
		% lname)

    else:
    #{
	# We're assigning velocities.

	# Find how many layers need ranges assigned,
	# and how much room is left
	count = 0
	unused  = 127
	for (lname, lvel, lrange, latten) in layers:
	    if lrange == -1:
	        count += 1
	    else:
	        unused -= lrange

	if unused < 0:
	    print >>sys.stderr, "Total of velocity ranges must not exceed 127"
	    sys.exit(1)

	# allocate unused velocity range to layers without vel-range specs
	ix = 0
	for (lname, lvel, lrange, latten) in layers:
	    if lrange == -1:
	        lrange = unused / count
		count -= 1
		unused -= lrange
		layers[ix] = (lname, lvel, lrange, latten)
	    ix += 1

	# assign specific max velocities to each
	ix = 0
	last_lvel = 0
	for (lname, lvel, lrange, latten) in layers:
	    last_lvel += lrange
	    layers[ix] = (lname, last_lvel, lrange, latten)
	    print >>sys.stderr, (
	        "Layer %*s: velocity %3d, range %3d"
		% (gl.lnamelen, lname, last_lvel, lrange))
	    ix += 1

    #}

    # build LAYER array
    for (lname, lvel, lrange, latten) in layers:
	LAYER.append((lname, lvel, latten))

#}


#             name   MIDI velocity	atenuation (dB x 10)
# LAYER.append(("s3",	 17,		220))


# Module initialization

def usage(prog):
    print >>sys.stderr
    print >>sys.stderr, "%s: create keyboard map for building a soundfont" % prog
    print >>sys.stderr
    print >>sys.stderr, "usage: %s <sfname> {sampfile}" % prog
    print >>sys.stderr
    print >>sys.stderr, "  where:"
    print >>sys.stderr, "     <sfname>   specifies input and output:"
    print >>sys.stderr, "                   <sfname>.sfc is the input (config),"
    print >>sys.stderr, "                   <sfname>.sfk is the output (keymap)."
    print >>sys.stderr, "     {sampfile} is any number of sample filenames, with UNIX wildcards"
    print >>sys.stderr, "     mapfile    is the output file name"
    print >>sys.stderr
    print >>sys.stderr, "  Output is ASCII text, and includes a char-graphic keyboard map layout"
    print >>sys.stderr
    sys.exit(1)




# Main

if __name__ == "__main__":

    args = sys.argv
    prog = args[0].split("\\")[-1]
    del args[0]

    if len(args) < 2:
        usage(prog)
	sys.exit(1)

    sfname = args[0]
    del args[0]

    ofname = sfname + ".sfk"
    cfname = sfname + ".sfc"
    try:
	gl.ofile = file(ofname, "w")
    except Exception, msg:
	print >>sys.stderr, msg
	sys.exit(1)

    print >>sys.stderr, "Input (control) file:", cfname
    print >>sys.stderr, "Output (keymap) file:", ofname

    process_cfg(cfname)
    build_grid(gl.grid)
    load_filenames(args)
    assign_keys(map)
    showmap(gl.grid, LAYER)
    emit_map(gl.grid, LAYER)

