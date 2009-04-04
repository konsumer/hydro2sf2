#!python
#
# Read & dump RIFF file.
# Make guesses about chunks

import sys

majors = (
    "RIFF",
    "LIST",
    "INFO",
    )

dbg = True

def get_sint16(file):
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

def roundup(ln):
    if ln & 1:
        return ln + 1
    return ln

class Chunk:
    def __init__(self, riffFile, parent):
	self.parent = parent
	self.riff   = riffFile
	self.subchunks = []

	if parent == None:
	    self.level = 0
	else:
	    self.level = parent.level + 1

    def ind(self):
        str = ""
	for ix in range(0, self.level):
	    str += " "
	return str
   
    def iseek(self):
        self.riff.inf.seek(self.inf_loc)

    def inf(self):
        return self.riff.inf

    def read(self):
        self.format	= self.riff.inf.read(4)
        self.len	= get_uint32(self.riff.inf)
	self.inf_loc	= self.riff.inf.tell()	# location of value

	if dbg:
	    print "0x%08x: %s %s" %(self.inf_loc - 8, self.ind(), self.format),
	    print "len: 0x%08x" % self.len,

	if self.format not in majors:
	    if dbg:
		print "loc: 0x%08x" % self.inf_loc
	    self.riff.inf.seek(self.inf_loc + roundup(self.len), 0)
	    return 8 + roundup(self.len)

	self.type = self.riff.inf.read(4)
	self.inf_loc += 4
	if dbg:
	    print "type:", self.type,
	    print "loc: 0x%08x" % self.inf_loc

	ln = 4
	while ln < self.len - 1:
	    chunk = Chunk(self.riff, self)
	    chunklen = chunk.read()
	    if ln + chunklen > self.len:
	        print "Error: last chunk exceeded parent's len"
		sys.exit(1)
	    self.subchunks.append(chunk)
	    ln += chunklen
	    # print self.ind(), "-- %s at 0x%08x, ln = 0x%08x" % (self.format, self.inf_loc + ln, ln)

	if self.len != roundup(ln):
	    print "Error: insufficient data"

	return roundup(self.len + 8)

    def printHdr(self):
	print "0x%08x: %s %s" %(self.inf_loc - 8, self.ind(), self.format),
	print "len: 0x%08x" % self.len,
	if "type" in dir(self):
	    print "type:", self.type
	else:
	    print

    def walk(self, func, arg=None):
        func(self, arg)
	for chunk in self.subchunks:
	    chunk.walk(func, arg)

    def prn(self, text):
	print "%11s %s %s" % ("", self.ind(), text)

    def prnLoc(self, text):
	print "0x%08x %s %s" % (self.inf_loc, self.ind(), text)

class RiffFile:

    def __init__(self, inf=None, outf=None):
        self.inf	= inf
	self.inf_ix	= 0
	self.outf	= outf
	self.outf_ix	= 0
	self.vsize	= None

    def read(self):
        if not self.inf:
	    return
	self.chunk = Chunk(self, None)
	self.chunk.read()

    def walk(self, func, arg=None):
        if "chunk" in dir(self):
	    self.chunk.walk(func, arg)


def main(args):
    if len(args) < 2:
        print "usage: %s <infile> -- dumps RIFF file"
	print
	sys.exit(1)

    infname = args[1]
    del args[1]

    try:
	inf  = file(infname, "rb")
    except IOError, msg:
        print msg
	sys.exit(1)

    riff = RiffFile(inf)
    riff.read()

if __name__ == "__main__":

    main(sys.argv)
