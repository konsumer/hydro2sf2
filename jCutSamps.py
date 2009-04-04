# Chop a wave file into separate sample files.
# For use in building soundfonts.
#
# If we add an option to omit detecting the pitch, it could
# be used for chopping a set into individual songs.  We'd
# also want to adjust the lead time to a second or two.

import sys
import math
import time
import profile
import warnings
import glob

import jwave
import jtime
import jmidi

# user configurable parameters

_trig_db	= -18.0		# dB, trigger level
_default_noise	= -50.0		# dB, default noise level when can't measure it.
_noise_delta	= 1.0		# dB, level above initial noise level to find sample end
_dwell_time	= 0.5		# seconds of sample to keep after level reaches noise level
_lead_time	= 0.0		# seconds to keep before start of note
_min_duration	= 1.00		# seconds, minimum note duration.

_folder		= ""
_fn_prefix	= ""
_fn_suffix	= ""


# constants

_min_freq	= 27		# Hz, lowest note frequency
_max_freq	= 4410		# Hz, highest note frequency (4186.0 = C8)

# tweak parameters

_calcs_per_sec	= 5		# Number of RMS calcs per second, to detect note end
_lead_crossings	= 2		# Number of zero crossings to find start of note


# Operating controls

_log_pitch	= False
_dry_run	= False		# if True, don't actually create any files.
_find_note	= True		# whether to add note number to file names

_debug		= False
_verbose	= True

# Find the next sample
def find_trigger(wave, start_sn, trig_dB):
    trigger = wave.dB2v(trig_dB)
    samp_num = start_sn
    wave.seekSample(samp_num)
    while True:
	try:
	    samp = wave.readSample()
	except IndexError:
	    return 0
	if abs(samp[0]) > trigger:
	    break;
	samp_num += 1

    # we've found a trigger.
    return samp_num

#
# Measure the RMS level starting at the given sample, for the given duration.
#
def measure_rms(wave, start_sn, duration):

    if duration < wave.fmt.sampleRate / 200:
        return 0.0

    wave.seekSample(start_sn)
    buf = jwave.Rmsbuf(wave)

    for samp_num in range(start_sn, start_sn + duration):
	samp = wave.readSample()
	buf.add(buf, samp[0])

    return buf.getRms()


def r(samps, delta, length):
    sum = 0L
    for sn in range(1, length):
	sum += abs(samps[sn] - samps[sn + delta])
    return sum

def find_pitch(wave, start):
    global _pitchlog

    start += wave.fmt.sampleRate / 4

    # Get a buffer of samples for finding the pitch
    end = min(wave.numSamples-1, start + 4 * wave.fmt.sampleRate)
    samps = wave.readChan(0, start, end)
    buflen = len(samps)

    # autocorrelation method for finding pitch
    # Define the autocorrelation function r(delta) defined as the sum of the
    # pointwise absolute difference between the val(t) and val(t + delta).
    # Find the lowest local minimum in r(delta).
    # Ignore noise in r(delta) using a latch filter with a miniumum deadband
    # (# samples elapsed since the minimum changed)

    # find the first sustained maximum.

    latch = 3

    maxr = 0L
    maxt = 0
    step = 12.0
    rate = 1.0 * wave.fmt.sampleRate
    note = 100.0

    delta = 4

    # for delta in range(wave.fmt.sampleRate / _max_freq, wave.fmt.sampleRate / _min_freq):
    while delta < wave.fmt.sampleRate / _min_freq:

	cur = r(samps, delta, buflen / 2)
	if _log_pitch:
	    print >>_pitchlog, wave.fmt.sampleRate / delta, ",", cur

	if cur > maxr:
	    maxr = cur
	    maxt = delta
	if maxt != 0 and delta - maxt >= latch:
	    break

	d2 = int(rate / pow(2, (step * math.log(rate / delta, 2) - 1) / step))
	delta = max(d2, delta + 1)
	last_note = note
	note = 12 * math.log(rate/delta)
	# print "delta = %d, f = %d, note = %5.1f, diff = %5.1f" % (
	#     delta, rate/delta, note, last_note - note)

    else:
	print "    Can't find pitch (2)."
	print "    maxt", maxt
	print "    delta", delta
	print "    latch", latch
	return 0
	# raise Exception("Sample too short (1)")

    # find the next local minumum.

    minr = 0x7fffffffffffffffL
    mint = 0
    limit = maxr / 3
    # for delta in range(delta + 1, wave.fmt.sampleRate / _min_freq):
    while delta < wave.fmt.sampleRate / _min_freq:

	cur = r(samps, delta, buflen / 2)
	if _log_pitch:
	    print >>_pitchlog, wave.fmt.sampleRate / delta, ",", cur

	if cur < minr:
	    minr = cur
	    mint = delta
	if mint != 0 and delta - mint >= latch:
	    if minr < limit:
		if not _log_pitch:
		    break

	d2 = int(rate / pow(2, (step * math.log(rate / delta, 2) - 1) / step))
	delta = max(d2, delta + 1)
	last_note = note
	note = 12 * math.log(rate/delta)
	# print "delta = %d, f = %d, note = %5.1f, diff = %5.1f" % (
	#     delta, rate/delta, note, last_note - note)

    else:
	print
	print "    Can't find pitch (2)."
	print "    start", start
	print "    maxr", maxr
	print "    maxt", maxt
	print "    minr", minr
	print "    mint", mint
	print "    delta", delta
	print "    latch", latch
	return 0
	# if not _log_pitch:
	    # raise Exception("Sample too short (2)")

    return wave.fmt.sampleRate / float(mint)


# find nth zero crossing (looking forward or backward)
#
# Note: only backwards has been used yet

def find_nth_zero(wave, start_sn, end_sn, slope=1, count=_lead_crossings):

    if start_sn < end_sn:
	first_sn = start_sn
	last_sn = end_sn + 1
	start_ix = 0
	stop_ix = last_sn - first_sn
	incr = 1
    else:
	first_sn = end_sn
	last_sn = start_sn + 1
	start_ix = last_sn - first_sn - 1
	stop_ix = 0
	slope = -slope
	incr = -1

    # read samples into buffer
    samps = []
    wave.seekSample(first_sn)
    for sn in range(first_sn, last_sn):
        samps.append(wave.readSample()[0])

    last = samps[start_ix]
    best = 0
    for ix in range(start_ix + incr, stop_ix, incr):
	this = samps[ix]
	# print first_sn + ix, this	##################################
	if last * slope < 0 and this * slope >= 0:
	    # print first_sn + ix, last, this, slope
	    count -= 1
	    best = first_sn + ix
	    if count == 0:
		return(first_sn + ix)
	last = this

    if best != 0:
        return best

    if True:
	print "  start_sn ", start_sn
	print "  end_sn   ", end_sn
	print "  slope    ", slope
    raise Exception("No zero crossing found with required slope")


def find_end(wave, start_sn, noise, dwell_t):
    calc_interval = wave.fmt.sampleRate / _calcs_per_sec
    noise = max(noise, -60.0)

    buf = jwave.Rmsbuf(wave, calc_interval)
    start_sn
    wave.seekSample(start_sn)
    sn = 1

    while True:
	try:
	    buf.add(buf, wave.readSample()[0])
	except IndexError:
	    print "  Sample ends before silence"
	    return (start_sn + sn, buf.getPeak())
	if sn % calc_interval == 0:
	    rms = buf.getRms()
	    if rms < noise:
		end_sn = min(start_sn + sn, wave.numSamples - 1)
		return (end_sn, buf.getPeak())
	sn += 1

    raise Exception("Can't find sample end")


def copy_wave(iwave, start_sn, end_sn, file_num, freq, sn_ratio, peak, duration):
    global _logfile

    if freq == 0:
        mnote = 0
	notename = "X%02d" % file_num
	cents = 0
    else:
	(mnote, notename, cents) = jmidi.midi_note_for_freq(freq)

    fname = (
        _folder
	+ _fn_prefix
	+ "%03d_" % mnote
	+ notename
	# + "_"
	# + "%+03d_" % cents
	# + "%07.2fHz_" % freq
	# + "%03.0fdB_" % sn_ratio
	# + jtime.sm(duration, iwave.fmt.sampleRate) + "s"
	+ _fn_suffix
	+ ".wav")
    print "File %3d:" % file_num, fname

    print >>_logfile, _fn_prefix	\
	,",", file_num 			\
	,",", mnote 			\
	,",", notename.strip("_")	\
	,",", "%+03d" % cents 		\
	,",", "%7.2f" % freq		\
	,",", "%4.1f" % sn_ratio	\
	,",", "%4.1f" % peak		\
	,",", jtime.sm(duration, iwave.fmt.sampleRate) + "s"

    if not _dry_run:
	ofile = file(fname, "wb")
	owave = jwave.WaveChunk(outf = ofile)
	owave.copyHeader(iwave)
	# owave.setNote(mnote)
	owave.writeHeader(end_sn + 1 - start_sn)
	owave.copySamples(iwave, start_sn, end_sn)


# find first zero crossing before trig_sn, where
# the difference bewteen two successive samples is less than
# twice the default noise level.

def find_start(wave, trig_sn, start_sn):

    vbose = True
    if vbose:
        print "   ",

    # read channel 1 samples into buffer

    samps = []
    wave.seekSample(start_sn)
    for sn in range(start_sn, trig_sn):
        samps.append(wave.readSample()[0])

    end_ix = len(samps) - 1
    last = samps[end_ix]

    noise = wave.dB2v(_default_noise) * 8

    for ix in range(end_ix - 1, 0, -1):

        this = samps[ix]

	if -noise < this < noise:
	    if vbose:
		print ".",
	    if abs(this - last) < noise:
		if vbose:
		    print
		return start_sn + ix

        last = this

    raise Exception("Can't find start of sample")


def old_find_start(wave, trig_sn, start_sn):

    # read channel 1 samples into buffer

    samps = []
    wave.seekSample(start_sn)
    for sn in range(start_sn, trig_sn):
        samps.append(wave.readSample()[0])

    # find N samples in a row whose values are less than default noise

    N = 3
    count = 0

    start_ix = len(samps)

    noise = wave.dB2v(_default_noise)

    for ix in range(start_ix - 1, 0, -1):

	# print "%6d %6d" % (ix, this)

	if abs(samps[ix]) < noise:
	    # print ".",
	    count += 1
	    if count == N:
	        return start_sn + ix
        else:
	    count = 0

    raise Exception("Start of sample not found")

def process_samples():
    global _default_noise

    try:
	inf  = file(_infile, "rb")
    except IOError, msg:
        raise IOError(msg)

    riff = jwave.RiffChunk(inf)
    riff.readHeader()
    riff.printHeader()
    # if riff.type != "riff":
    #     print "Unsupported format (only wave files supported)"
    #     return 1

    wave = jwave.WaveChunk(riff=riff, inf=inf)
    wave.readHeader()
    wave.printHeader()
    rate = wave.fmt.sampleRate

    if wave.fmt.compCode != 1:
        print "Compressed formats unsupported"
        sys.exit(1)

    print
    file_num = 1
    end_sn = 1
    while True:
        t = jtime.start()

	# 1) find the next peak that exceeds the trigger level

	trig_sn = find_trigger(wave, end_sn, trig_dB=_trig_db)
	if trig_sn == 0:
	    return		## EOF, we're done.

	if _verbose:
	    print
	    print "    trig_sn      ", trig_sn, jtime.hmsm(trig_sn, rate)

	# 2) Starting from the trigger point, search backwards to find the
	#    first positive sloped zero crossing.  Search at most a fraction of a second.

	end_sn = max(end_sn, trig_sn - rate/10)
	# start_sn = find_nth_zero(wave, trig_sn, end_sn, slope=1)
	start_sn = find_start(wave, trig_sn, end_sn)
	start_sn = max(1, start_sn - int(_lead_time * rate))

	if _verbose:
	    print "    start_sn     ", start_sn, jtime.hmsm(start_sn, rate)

	# 3) Back up at most a second and measure a half-second of noise

	noise_sn = max(1, start_sn - rate)
	dur = min(rate / 2, (start_sn - noise_sn) / 2)
	noise_lev = measure_rms(wave, noise_sn, dur)
	if noise_lev == None:
	    print "  Can't measure noise, using %5.2f dB" % _default_noise
	    noise_lev = _default_noise
        else:
	    # use this value if we can't measure it later
	    _default_noise = noise_lev

	if _verbose:
	    print "    noise_lev    ", noise_lev

	# 4) Find where the sample ends:
	#    where the RMS level matches the initial noise level plus a delta,
	#    plus a dwell time.
	(end_sn, peak_lev) = find_end(wave, trig_sn, noise_lev + _noise_delta, _dwell_time)

	duration = end_sn - start_sn
	if _verbose:
	    print "    end_sn       ", end_sn, jtime.hmsm(end_sn, rate)
	    print "    duration     ", jtime.sm(duration, rate)

	if duration < _min_duration * wave.fmt.sampleRate:
	    if _verbose:
		print "    Skipping .. too short"
		print
	    continue


	# 5) Find which note the sample is
	if _find_note:
	    freq = find_pitch(wave, trig_sn)

	if _verbose:
	    print "    freq         ", freq
	    print

	# 6) Record results & copy wave data

	if _debug:
	    print
	    print "%3d freq: %-6.1f floor:%5.1f peak:%5.1f S/N: %-5.1f start:%d=%9s dur:%9s" % (
		file_num,
		freq,
		noise_lev,
		peak_lev,
		peak_lev - noise_lev,
		start_sn, jtime.msm(start_sn, rate),
		jtime.msm(duration, rate))

	copy_wave(wave, start_sn, end_sn, file_num, freq, peak_lev - noise_lev, peak_lev, duration)
	file_num += 1

	t = jtime.end(t)
	print
	print "    Elapsed time:", jtime.msm(t, 1)

def usage(prog):
    print >>sys.stderr
    print >>sys.stderr, "%s: cut wave file into individual samples" % prog
    print >>sys.stderr
    print >>sys.stderr, "  Usage: %s {[-f <outfolder>] {<wavefile>}}" % prog
    print >>sys.stderr
    print >>sys.stderr, "where:"
    print >>sys.stderr, "  { x } means 'any number of x'"
    print >>sys.stderr, "  -f <outfolder> specifies the output folder for"
    print >>sys.stderr, "     sample files for following input wave files."
    print >>sys.stderr, "  <wavefile> is a wave file containing mutliple"
    print >>sys.stderr, "     samples.  Unix-style globbing is permitted,"
    print >>sys.stderr, "     that is, you can use '*.wav' or 'samp*/my*foo.wav'."
    print >>sys.stderr
    sys.exit(1)


def main(prog, args):
    global _fn_prefix
    global _fn_suffix
    global _infile
    global _folder
    global _pitchlog
    global _logfile

    rCode = 0

    if len(args) < 1:
        usage(prog)
	return 1

    if _log_pitch:
	print "OPENING PITCH LOG"
	_pitchlog = open("pitch.csv", "w")

    t1 = jtime.start()
    file_count = 0

    while len(args) > 0:

	if len(args) > 2 and args[0] == "-f":
	    _folder = args[1] + "/"
	    print "Output folder:", args[1]
	    del args[0]
	    del args[0]

	if len(args) < 1:
	    return rCode

	fspec = args[0]
	del args[0]

	for _infile in glob.glob(fspec):

	    file_count += 1
	    print "\nProcessing", _infile, "==================================="
	    print

	    # Split the file name into prefix (inst name) and suffix (velocity)

	    basename = _infile.split(".")[0]	# strip ".wav"
	    parts = basename.split("_")
	    _fn_prefix = parts[0] + "_"
	    del parts[0]
	    _fn_suffix = "_" + "_".join(parts)
	    print "prefix =", _fn_prefix
	    print "suffix =", _fn_suffix

	    _logfile = open(_folder + _fn_prefix + _fn_suffix[1:] + "_log.csv", "w")
	    print >>_logfile, "fn_prefix"	\
		,",", "file_num" 		\
		,",", "mnote"		\
		,",", "notename" 		\
		,",", "cents" 		\
		,",", "freq"		\
		,",", "sn_ratio"		\
		,",", "peak"		\
		,",", "duration"

	    t2 = jtime.start()
	    try:
		if prof:
		    rCode = profile.run("process_samples()")
		else:
		    rCode = process_samples()
	    except IOError, msg:
		print msg
		if len(args) > 0:
		    print "Skipping ..."
		    continue

	    print
	    print "Elapsed time for %s: " % _infile, jtime.hms(jtime.end(t2), 1)

	    _logfile.close()

    if file_count > 1:
	print
	print "Elapsed time for all files:", jtime.hms(jtime.end(t1), 1)

    return rCode


prof = False
if __name__ == "__main__":

    warnings.filterwarnings("default", ".*")
    # warnings.filterwarnings("error", ".*")

    args = sys.argv
    prog = args[0].split("\\")[-1]
    del args[0]

    # command line mode
    rCode = main(prog, args)
    sys.exit(rCode)


    ### Maybe later.  Works but I don't like it.

    while True:

	print "Args: (^C to exit)",

	try:
	    print
	    main(sys.stdin.readline())
	    print
	except KeyboardInterrupt:
	    sys.exit(0)

