
import struct

# structure: list of (name, type, (typeargs)), one for each field
#
# types:	typeargs
#   String	len (None means no limit)
#   Sint8	
#   Uint8	
#   Sint16
#   Uint16
#   Sint32
#   Uint32
#   Sint32
#   Struct	list of Field
#   

# default endian-ness
_little_endian = True

class Type:
    def __init__(self, args=None):
	if _little_endian:
	    self.endian = "<"
	else:
	    self.endian = ">"
	self.Len = 0

    def read(self, inf):
	return struct.unpack(self.fmt, inf.read(self.Len))[0]

    def writeval(self, val, outf):
        outf.write(struct.pack(self.fmt, val))
	return(self.Len)

    def var(self, args=None):
        return Var(self, args)

    def initval(self, assigntype, val):
        if val == None:
	    return None
	if isinstance(val, type(self)):
	    if val.type == self:
		return val
	    else:
	        raise Exception("type mismatch")
	return _noval	# means "I couldn't do it, hope you can!"

    def str(self, val, ident=None):
        return str(val)

    # return packed (file) size of data type
    def size(self, var=None):
        return self.Len

    # save members as Python attributes
    def structify(self, var):
        # nothing to do for simple types
	return

class Sint8(Type):
    def __init__(self, args=None):
	Type.__init__(self, args)
	self.fmt = self.endian + "b"
	self.Len = 1

class Uint8(Type):
    def __init__(self, args=None):
	Type.__init__(self, args)
	self.fmt = self.endian + "B"
	self.Len = 1

    def str(self, val):
        return "0x%02x" % val

class Sint16(Type):
    def __init__(self, args=None):
	Type.__init__(self, args)
	self.fmt = self.endian + "h"
	self.Len = 2

class Uint16(Type):
    def __init__(self, args=None):
	Type.__init__(self, args)
	self.fmt = self.endian + "H"
	self.Len = 2

    def str(self, val):
        return "0x%04x" % val

class Sint32(Type):
    def __init__(self, args=None):
	Type.__init__(self, args)
	self.fmt = self.endian + "l"
	self.Len = 4

class Uint32(Type):
    def __init__(self, args=None):
	Type.__init__(self, args)
	self.fmt = self.endian + "L"
	self.Len = 4

    def str(self, val):
        return "0x%08x" % val

# char array.  args = string length

class ChArray(Type):
    def __init__(self, args):
	Type.__init__(self, args[1:])
	self.Len = args[0]
	self.fmt = str(self.Len) + "s"

    def read(self, inf):
	val = struct.unpack(self.fmt, inf.read(self.Len))[0]
	ix = val.find("\000")
	if ix >= 0:
	    val = val[0:ix]
	return val

    def writeval(self, val, outf):
        val = val.rstrip("\000") + "\000"
	if len(val) & 1:
	    val += "\000"
	return Type.writeval(self, val, outf)


class Enum16(Uint16):
    def __init__(self, vlist):
        Uint16.__init__(self, None)
        self.val2text = {}
        self.text2val = {}
	for (val, text) in vlist:
	    self.val2text[val] = text
	    self.text2val[text] = val

    def str(self, val):
	if val not in self.val2text:
	    return Uint16.str(self, val)
	return self.val2text[val]

    def val(self, text):
	if val not in self.text2val:
	    raise Exception("invalid enum text value")
	return self.text2val[text]

    def writeval(self, val, outf):
	if type(val) is int:
	    return Uint16.writeval(self, val, outf)
        raise Exception("writeval for enum names NYI")

class Field:
    def __init__(self, fdef):
        (self.name, self.type) = fdef

class Struct(Type):
    def __init__(self, name, flist):
	self.name   = name
	self.fields = []
	self.fieldsbyname = {}	
	self.Len    = 0
        for fdef in flist:
	    field = Field(fdef)
	    self.fields.append(field)
	    self.fieldsbyname[field.name] = field
	    self.Len += field.type.Len

    def initval(self, assigntype, val):
        rval = Type.initval(self, assigntype, val)
	if rval != (None,):
	    return rval

	for field in val:
	    # FIXME
	    pass

    def read(self, inf):
	rval = []
        for field in self.fields:
	    rval.append(field.type.read(inf))
	return rval

    def writeval(self, val, outf):
	slen = 0
	ix = 0
        for field in self.fields:
	    # print "Struct.writeval:", val[ix], "type", field.type
	    slen += field.type.writeval(val[ix], outf)
	    ix += 1
	return slen

    def walk(self, func, args=None, level=0):
        level += 1
        for field in self.fields:
	    func(field.name, field.type, args, level)		# %%%
	    if isinstance(field.type, Struct):
	        field.type.walk(func, args, level)		# %%%

    def walkval(self, val, func, args=None, level=0, ident=None):
	name = self.name
	if ident:
	    name += " " + ident
	func(name, self, None, args, level)
	if val == None:
	    return
	if len(val) != len(self.fields):
	    print "%%% val = ", val
	    raise Exception("ill-formed value for struct")

        level += 1
	ix = 0
        for field in self.fields:
	    fval = val[ix]
	    func(field.name, field.type, fval, args, level)
	    if isinstance(field.type, Struct):
	        field.type.walk(func, fval, val, args, level)
	    ix += 1

    def str(self, val):
        return ""

    def size(self):
	slen = 0
        for field in self.fields:
	    slen += field.type.size()
	return slen

    # save members as Python attributes
    def structify(self, var):
	if var.val == None:
	    for field in self.fields:
		setattr(var, field.name, None)
	    return

	if len(self.fields) != len(var.val):
	    raise Exception("struct var value doesn't match fields")
	ix = 0
        for field in self.fields:
	    # %%% should make this recursive to handle structs in structs
	    # %%% kluge: struct shouldn't know about enum
	    if isinstance(field.type, Enum16):
		setattr(var, field.name, field.type.str(var.val[ix]))
	    else:
		setattr(var, field.name, var.val[ix])
	    ix += 1

class Var:
    def __init__(self, type, args=None):
	self.type = type
        self.val = type.initval(type, args)
	if self.val == _noval:
	    # for now, let's try trust!
	    self.val = args

    def walk(self, func, args=None, level=0, ident=None):
        self.type.walkval(self.val, func, args, level, ident)

    def structify(self):
        self.type.structify(self)


# standard types:

sint8  = Sint8()
uint8  = Uint8()
sint16 = Sint16()
uint16 = Uint16()
sint32 = Sint32()
uint32 = Uint32()

_notype	= Type()
_noval  = (None,)		# kluge so next line will work 
_noval  = Var(_notype)		# marker for special cases only

if __name__ == "__main__":

    # main(sys.argv)
    pass

