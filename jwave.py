# Handle Microsoft RIFF chunks, as in wave files.

import math
import time
import profile
import warnings

import struct

import jtime

def v2dB(v):
    if (v == 0):
        return None
    return 20.0 * math.log10(abs(v))

def v2dB24(v):
    return v2dB((float(v))/0x7fffff)

def v2dB16(v):
    return v2dB((float(v))/0x7fff)

def dB2v24(db):
    return int(math.exp(db * math.log(10) / 20) * 0x7fffff)

def dB2v16(db):
    return int(math.exp(db * math.log(10) / 20) * 0x7fff)

def get_sint24(ifile):
    bytes = ifile.read(3)        
    val = (((
        ord(bytes[2]) << 8)
        + ord(bytes[1]) << 8)
        + ord(bytes[0]))
    if val >= 0x800000:
        return val - 0x1000000
    return val

def put_sint24(ofile, val):
    bytes = ""
    bytes += chr(val & 0xff)
    val = val >> 8
    bytes += chr(val & 0xff)
    val = val >> 8
    bytes += chr(val & 0xff)
    ofile.write(bytes)

def get_sint16(file):
    # return struct.unpack("<h", file.read(2))[0]
    val = get_uint16(file)
    if val >= 0x8000:
        return val - 0x10000
    return val

def put_sint16(file):
    bytes = ""
    bytes += chr(val & 0xff)
    val = val >> 8
    bytes += chr(val & 0xff)
    ofile.write(bytes)

def get_sint8(file):
    print "8-bit format unsupported"
    sys.exit(1)

def get_uint32(file):
    bytes = file.read(4)
    return ((((0L
        + ord(bytes[3]) << 8)
        + ord(bytes[2]) << 8)
        + ord(bytes[1]) << 8)
        + ord(bytes[0]))

def put_uint32(ofile, val):
    bytes = ""
    bytes += chr(val & 0xff)
    val = val >> 8
    bytes += chr(val & 0xff)
    val = val >> 8
    bytes += chr(val & 0xff)
    val = val >> 8
    bytes += chr(val & 0xff)
    ofile.write(bytes)

def get_uint24(file):
    bytes = file.read(3)        
    return (((
        ord(bytes[2]) << 8)
        + ord(bytes[1]) << 8)
        + ord(bytes[0]))

def get_uint16(file):
    # return struct.unpack("<H", file.read(2))[0]
    bytes = file.read(2)
    return (ord(bytes[1]) << 8) + ord(bytes[0])

def put_uint16(ofile, val):
    bytes = ""
    bytes += chr(val & 0xff)
    val = val >> 8
    bytes += chr(val & 0xff)
    ofile.write(bytes)

def get_uint8(file):
    return ord(file.read(1))

class Chunk:

    def __init__(self, inf=None, outf=None):
        self.type = None
        self.inf = inf
        self.outf = outf
        self.data = []
        self.readIx = 0
        self.writeIx = 0
        self.chunks = {}

    def readHeader(self):
        self.type = self.inf.read(4)

    def writeHeader(self):
	# print "writing header:", self.type
	self.outf.write(self.type)

    def printHeader(self):
        print self.type,


class RiffChunk(Chunk):
    def __init__(self, inf=None, outf=None):
        Chunk.__init__(self, inf, outf)
        
    def readHeader(self):
        Chunk.readHeader(self)
        self.size = get_uint32(self.inf)
        
    def writeHeader(self):
        Chunk.writeHeader(self)
	# print "writing size: 0x%08x" % self.size
        put_uint32(self.outf, self.size)
        
    def printHeader(self):
        Chunk.printHeader(self)
        print  "size = 0x%x" % self.size


class WaveChunk(Chunk):
    def __init__(self, riff=None, inf=None, outf=None):
        Chunk.__init__(self, inf, outf)
	self.riff = riff
        
    def readHeader(self):
        Chunk.readHeader(self)
        fmt = RiffChunk(self.inf)
        fmt.readHeader()
        if fmt.type != "fmt ":
            print "%%%%error: fmt chunk wasn't first"
            sys.exit(1)
        if fmt.size < 16:
            print "%%%%error: fmt chunk too small"
            sys.exit(1)
        fmt.compCode       = get_uint16(self.inf)
        fmt.numChan        = get_uint16(self.inf)
        fmt.sampleRate     = get_uint32(self.inf)
        fmt.aveBytesPerSec = get_uint32(self.inf)
        fmt.blockAlign     = get_uint16(self.inf)
        fmt.bitsPerSample  = get_uint16(self.inf)
        if fmt.size > 16:
            fmt.extraFmtBLen  = get_uint16(self.inf)
            fmt.extraFmtBytes = self.inf.read(fmt.extraFmtBLen)
           
        self.fmt = fmt
        bytesPerVal = (fmt.bitsPerSample + 7) / 8
	self.bytesPerVal = bytesPerVal
	if (bytesPerVal * fmt.numChan != fmt.blockAlign):
	    print ("Unsupported format: bytesPerVal = %d, blockAlign = %d, numChan = %d" %
		(bytesPerVal, fmt.blockAlign, fmt.numChan))
	    sys.exit(1)
        if bytesPerVal == 2:
	    self.setup16()
        elif bytesPerVal == 3:
	    self.setup24()
        else:
            print "Unsupported format"
            sys.exit(1)
            
	while True:
	    data = RiffChunk(self.inf)
	    data.readHeader()
	    if data.type == "data":
	        break
	    print "Skipping unexpected WAVE file chunk:",
	    data.printHeader()
	    self.inf.seek(data.size, 1)		# skip this chunk!
	    # %%% should save skipped (unrecognized) chunks
	else:
	    print "No wave data chunk found!"
	    sys.exit(1)

        self.data = data

        self.numSamples = self.data.size / self.fmt.blockAlign

        # self.start = self.inf.tell()		## %%% why doesn't this work ???
        self.start = 28 + fmt.size

    def writeHeader(self, nsamples=0):
	fmt = self.fmt
	self.riff.size = 28 + fmt.size + nsamples * fmt.blockAlign

	self.riff.writeHeader()
        Chunk.writeHeader(self)
    	fmt.writeHeader()
        put_uint16(self.outf, fmt.compCode)
        put_uint16(self.outf, fmt.numChan)
        put_uint32(self.outf, fmt.sampleRate)
        put_uint32(self.outf, fmt.aveBytesPerSec)
        put_uint16(self.outf, fmt.blockAlign)
        put_uint16(self.outf, fmt.bitsPerSample)
        if fmt.size > 16:
            fmt.extraFmtBLen  = put_uint16(self.outf, fmt.extraFmtBLen)
            fmt.extraFmtBytes = self.outf.write(fmt.extraFmtBytes)
           
        data = RiffChunk(outf=self.outf)
	data.type = "data"
	data.size = fmt.blockAlign * nsamples
        data.writeHeader()
        self.start = 28 + fmt.size

    # copy samples from given input wave file to self's output wave file
    # Assume seek has already happened on self
    def copySamples(self, iwave, start_sn, end_sn):
        if (iwave.fmt.blockAlign != self.fmt.blockAlign
	    or iwave.fmt.numChan != iwave.fmt.numChan
	    or iwave.fmt.bitsPerSample != self.fmt.bitsPerSample):
	    print "copySamples: wave formats must match"
	iwave.seekSample(start_sn)
	sampcount = end_sn + 1 - start_sn

	# test #####
	if False:
	    for ix in range(0,sampcount):
		samp = iwave.readSample()
		self.writeSample(samp)
	    return

	# fast way
	bytecount = sampcount * self.fmt.blockAlign
	blksize = 4096
	while bytecount > blksize:
	    self.outf.write(iwave.inf.read(blksize))
	    bytecount -= blksize
	self.outf.write(iwave.inf.read(bytecount))


    def copyHeader(self, src):
	self.riff	= src.riff
	self.riff.inf	= self.inf
	self.riff.outf	= self.outf
        self.type	= src.type

        fmt = RiffChunk(self.inf, self.outf)
        if src.fmt.type != "fmt ":
            print "%%%%error: copying non-wave to wave"
            sys.exit(1)

        fmt.type	   = src.fmt.type
        fmt.size	   = src.fmt.size
        fmt.compCode       = src.fmt.compCode
        fmt.numChan        = src.fmt.numChan
        fmt.sampleRate     = src.fmt.sampleRate
        fmt.aveBytesPerSec = src.fmt.aveBytesPerSec
        fmt.blockAlign     = src.fmt.blockAlign
        fmt.bitsPerSample  = src.fmt.bitsPerSample
        if src.fmt.size > 16:
            fmt.extraFmtBLen  = src.fmt.extraFmtBLen
            fmt.extraFmtBytes = src.fmt.extraFmtBytes

        self.fmt    = fmt
	self.getval = src.getval
	self.putval = src.putval
	self.dB2v   = src.dB2v
	self.v2dB   = src.v2dB

        data = RiffChunk(self.inf, self.outf)
        self.data = []
        self.start = 28 + fmt.size

    def setup16(self):
	self.getval = get_sint16
	self.putval = put_sint16
	self.dB2v   = dB2v16
	self.v2dB   = v2dB16

    def setup24(self):
	self.getval = get_sint24
	self.putval = put_sint24
	self.dB2v   = dB2v24
	self.v2dB   = v2dB24

    def printHeader(self):
        Chunk.printHeader(self)
        print
        print " ",
        self.fmt.printHeader()
        print "    compCode      =", self.fmt.compCode
        print "    numChan       =", self.fmt.numChan
        print "    sampleRate    =", self.fmt.sampleRate
        print "    blockAlign    =", self.fmt.blockAlign
        print "    bitsPerSample =", self.fmt.bitsPerSample
        if self.fmt.size > 16:
            print "    extraFmtBLen  =", self.fmt.extraFmtBLen
        print " ",
        self.data.printHeader()

        print "    (samples)     =", self.numSamples
        print "    (duration)    =", jtime.hmsm(
	    self.numSamples, self.fmt.sampleRate)


    def seekSample(self, n):
        loc = self.start + (n * self.fmt.blockAlign)
        self.inf.seek(loc)

    def getSample(self, n):
        loc = self.start + (n * self.fmt.blockAlign)
        self.inf.seek(loc)
        samp = []
        for ix in range(0, self.fmt.numChan):
            samp.append(self.getval(self.inf))
        return samp
    
    def readSample(self):
        samp = []
        for ix in range(0, self.fmt.numChan):
            samp.append(self.getval(self.inf))
        return samp

    def writeSample(self, samp):
        for ix in range(0, self.fmt.numChan):
            self.putval(self.outf, samp[ix])

    def readChan(self, chan, start, end):
	samps = []
	skip_bytes = (self.fmt.numChan - 1) * self.bytesPerVal
        loc = self.start + (start * self.fmt.blockAlign) + chan
        self.inf.seek(loc)
	# print "self.start =", self.start
	# print "loc =", loc
	# print "start, end", start, end
	if skip_bytes:
	    for sampn in range(start, end):
		samps.append(self.getval(self.inf))
		self.inf.read(skip_bytes)
	else:
	    for sampn in range(start, end):
		samps.append(self.getval(self.inf))

	return samps

    # sample generator -- not used
    def samples(self):
        while True:
            samp = []
            for ix in range(0, self.fmt.numChan):
                try:
                    v = self.getval(self.inf)
                except:
                    return
                samp.append(v)
            yield samp


class Rmsbuf:
    def __init__(self, wave, maxlen=0):
	if maxlen == 0:
	    maxlen = wave.fmt.sampleRate
        self.maxlen = maxlen
        self.calcInterval = wave.fmt.sampleRate / 10	# %%% should be 5
	self.v2dB = wave.v2dB
	self.dB2v = wave.dB2v

        self.data = []
        self.len = 0
        self.add = Rmsbuf.add_notfull
        self.maxval = 0
        self.maxrms = 0
        self.minrms = 0x7fffffff
        self.sumvsquared = 0L
        self.t = 0
	self.full = False

    def add_notfull(self, val):
        self.data.append(val)

	###
        # keep these lines same as below
        self.t += 1
        absval = abs(val)
        self.sumvsquared += (absval + 0L) * absval
        if absval > self.maxval:
            self.maxvt  = self.t
            self.maxval = absval
	###

        self.len += 1
        if self.len == self.maxlen:
            self.add = Rmsbuf.add_full
	    self.full = True
        self.index = self.maxlen - 1
        
    def add_full(self, val):
        self.index = (self.index + 1) % self.maxlen
        absold = abs(self.data[self.index]) + 0L
        self.sumvsquared -= absold * absold
        
	###
        # keep these lines same as above
        self.t += 1
        absval = abs(val)
        self.sumvsquared += (absval + 0L) * absval
        if absval > self.maxval:
            self.maxvt  = self.t
            self.maxval = absval
        ####
        
        self.data[self.index] = val
        if self.t % self.calcInterval == 0:
            rms = math.sqrt(self.sumvsquared / self.maxlen)
            # print "%s: %-7.3f" % (jtime.hms(self.t, self.maxlen), self.v2dB(rms))
	    if rms > self.maxrms:
		self.maxrmst = self.t
		self.maxrms = rms
	    if rms < self.minrms:
		self.minrmst = self.t
		self.minrms = rms

    def getRms(self):
	if self.sumvsquared < self.len * 2:
	    return self.v2dB(2)
	return self.v2dB(math.sqrt(self.sumvsquared / self.len))

    def getPeak(self):
	return self.v2dB(self.maxval)



def dbTest(wave):
    print "%9s %10s %9s" % ("dB", "dB2v(dB)", "v2dB(dB2v(dB))")
    for val in (0.0, -6.02, -12.04, -18.06, -48.16, -50.0, -90.31):
        print ("%9.5f 0x%08x %9.2f"
               % (val,
	          wave.dB2v(val),
                  wave.v2dB(wave.dB2v(val))
                  )
               )

def dbTest2(wave):
    for val in (0.25, 0.5, 0.75, 0.9999999):
        print ("%9.5f %9.2f -- 0x%6x  %9.2f"
               % (val, v2dB(val),
                  int(val * 0x7fffff),
                  wave.v2dB(int(val * 0x7fffff))
                  )
               )

def riffdump(args):
    if len(args) < 2:
        print "usage: %s <infile> <formatfile> -- dumps RIFF file" % args[0]
	print
	print "  <formatfile> contains a list of RIFF chunk names of"
	print "  chunks containing subchunks."
	sys.exit(1)

    infname = args[1]
    del args[1]

    try:
	inf  = file(infname, "rb")
    except IOError, msg:
        print msg
	sys.exit(1)

    riff = RiffChunk(inf)
    riff.readHeader()
    riff.printHeader()


if __name__ == "__main__":

    import sys
    riffdump(sys.argv)

