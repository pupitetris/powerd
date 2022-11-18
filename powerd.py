#!/usr/bin/python3

# pip3 install pyobjc

# Code based on https://benden.us/journal/2014/OS-X-Power-Management-No-Sleep-Howto/

import signal
import sys
import ctypes
import CoreFoundation
import objc
import subprocess


def SetUpIOFramework():
  # load the IOKit library
  iokit = ctypes.cdll.LoadLibrary(
    '/System/Library/Frameworks/IOKit.framework/IOKit')

  # declare parameters as described in IOPMLib.h
  iokit.IOPMAssertionCreateWithName.argtypes = [
    ctypes.c_void_p,  # CFStringRef
    ctypes.c_uint32,  # IOPMAssertionLevel
    ctypes.c_void_p,  # CFStringRef
    ctypes.POINTER(ctypes.c_uint32)]  # IOPMAssertionID
  iokit.IOPMAssertionRelease.argtypes = [
    ctypes.c_uint32]  # IOPMAssertionID
  return iokit


def StringToCFString(string):
  # we'll need to convert our strings before use
  return objc.pyobjc_id(
    CoreFoundation.CFStringCreateWithCString(None, string.encode('ascii'),
      CoreFoundation.kCFStringEncodingASCII).nsstring())


def AssertionCreateWithName(iokit, a_type,
                            a_level, a_reason):
  # this method will create an assertion using the IOKit library
  # several parameters
  a_id = ctypes.c_uint32(0)
  a_type = StringToCFString(a_type)
  a_reason = StringToCFString(a_reason)
  a_error = iokit.IOPMAssertionCreateWithName(
    a_type, a_level, a_reason, ctypes.byref(a_id))

  # we get back a 0 or stderr, along with a unique c_uint
  # representing the assertion ID so we can release it later
  return a_error, a_id


def AssertionRelease(iokit, assertion_id):
  # releasing the assertion is easy, and also returns a 0 on
  # success, or stderr otherwise
  return iokit.IOPMAssertionRelease(assertion_id)


def CreateAssertions(iokit, types):
  global VERBOSE

  reason = 'com.apple.metadata.mds_stores.power'
  kIOPMAssertionLevelOn = 255

  asserts = {}
  for typename in types:
    ret, a_id = AssertionCreateWithName(iokit, typename, kIOPMAssertionLevelOn, reason)
    if ret != 0:
      exit(1)
    asserts[typename] = a_id
    if VERBOSE:
      print('Created power assertion %s: status %s, id %s' % (typename, ret, a_id))

  return asserts


def RemoveAssertions(iokit, types, asserts):
  global VERBOSE

  for typename in types:
    if VERBOSE:
      print('\rReleasing power assertion %s: id %s' % (typename, asserts[typename]))
    AssertionRelease(iokit, asserts[typename])


def main():
  # Emulating caffeinate -s -i -d and powerd.
  types = ['PreventSystemSleep', 'PreventUserIdleSystemSleep', 'PreventUserIdleDisplaySleep']

  # first, we'll need the IOKit framework
  iokit = SetUpIOFramework()

  # next, create the assertions and save the IDs!
  asserts = CreateAssertions(iokit, types)

  if VERBOSE:
    # subprocess a call to pmset to verify the assertion worked
    subprocess.call(['pmset', '-g', 'assertions'])

  signal.sigwait([signal.SIGINT])

  RemoveAssertions(iokit, types, asserts)


if __name__ == '__main__':
  VERBOSE = (len(sys.argv) > 1 and sys.argv[1] == '-v')
  main()
