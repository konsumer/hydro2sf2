# equivalent of unix "tr"

import string

def tr(input, fromstr, tostr, deletechars=""):

    if len(tostr) < len(fromstr):
        pad = tostr[-1]
	while len(tostr) < len(fromstr):
	    tostr += pad
    trans = string.maketrans(fromstr, tostr)
    return(input.translate(trans, deletechars))
