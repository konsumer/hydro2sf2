
import time

def start():
    return time.time()

def end(t):
    return time.time() - t

def hmsm(samps, ticks_per_sec):
    duration = int((samps * 1000L) / ticks_per_sec)
    dur_hr   = duration / 3600000
    dur_min  = (duration % 3600000) / 60000
    dur_sec  = (duration % 60000) / 1000
    dur_msec = (duration % 1000)
    return "%02d:%02d:%02d.%03d" % (dur_hr, dur_min, dur_sec, dur_msec)

def hms(samps, ticks_per_sec):
    duration = int(samps / ticks_per_sec)
    dur_hr   = duration / 3600
    dur_min  = (duration % 3600) / 60
    dur_sec  = (duration % 60)
    return "%02d:%02d:%02d" % (dur_hr, dur_min, dur_sec)

def msm(samps, ticks_per_sec):
    duration = int((samps * 1000L) / ticks_per_sec)
    dur_min  =  duration / 60000
    dur_sec  = (duration % 60000) / 1000
    dur_msec = (duration % 1000)
    return "%02d:%02d.%03d" % (dur_min, dur_sec, dur_msec)

def sm(samps, ticks_per_sec):
    duration = int((samps * 1000L) / ticks_per_sec)
    dur_sec  =  duration / 1000
    dur_msec = (duration % 1000)
    return "%02d.%03d" % (dur_sec, dur_msec)

