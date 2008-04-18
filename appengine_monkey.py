import os
import imp
import sys

class Missing(object):
    def __init__(self, name):
        self.name = name
    def __call__(self, *args, **kw):
        raise NotImplemented('%s is not implemented' % self.name)
    def __repr__(self):
        return '<Missing function %s>' % self.name

def patch(module):
    def decorate(func):
        setattr(module, func.func_name, func)
        return func
    return decorate

os.utime = Missing('os.utime')
os.rename = Missing('os.rename')
os.unlink = Missing('os.unlink')
os.open = Missing('os.open')


def can_access(path):
    try:
        os.listdir(path)
        return True
    except OSError:
        return False

sys.path = [p for p in sys.path if can_access(p)]

@patch(imp)
def acquire_lock():
    pass

@patch(imp)
def release_lock():
    pass

@patch(imp)
def load_module(fullname, fp, filename, etc):
    pass

@patch(imp)
def find_module(subname, path):
    for p in path:
        full_py = os.path.join(p, subname + '.py')
        full_dir = os.path.join(p, subname, '__init__.py')
        for full in full_py, full_dir:
            if os.path.exists(full):
                return open(full), full, None
    return None, '', None

@patch(os)
def readlink(path):
    return path

# This is for the Mac pkg_resources when run in the SDK:
@patch(os)
def popen(*args, **kw):
    if not kw and args == ('/usr/bin/sw_vers',):
        # This is what pkg_resources uses to detect the version
        from StringIO import StringIO
        ## FIXME: somewhat lamely, all systems become 10.5.2
        return StringIO('ProductName:	Mac OS X\nProductVersion:	10.5.2\nBuildVersion:	000000')
    else:
        raise NotImplemented("os.open is not implemented")

# Again for Mac and pkg_resources:
@patch(os)
def uname():
    return ('AppEngine', 'appengine-host', '0.0.0', '#1', 'i386')

try:
    import pkg_resources
except ImportError:
    pass
else:
    if hasattr(os, '__loader__'):
        # This only seems to apply to the SDK
        pkg_resources.register_loader_type(type(os.__loader__), pkg_resources.DefaultProvider)

def patch_modules():
    file_dir = os.path.dirname(__file__)
    if os.path.exists(os.path.join(file_dir, 'appengine_monkey_files')):
        file_dir = os.path.join(file_dir, 'appengine_monkey_files')
    repl_dir = os.path.join(file_dir, 'module-replacements')
    if repl_dir not in sys.path:
        sys.path.insert(0, repl_dir)
    for module in ['httplib', 'subprocess', 'zipimport']:
        if (module in sys.modules
            and 'module-replacements' not in sys.modules[module].__file__):
            del sys.modules[module]

patch_modules()

import socket

class SocketError(Exception):
    pass
socket.error = SocketError

@patch(socket)
def _fileobject(socket_obj, mode='rb', bufsize=-1, close=False):
    ## FIXME: this is a fix for urllib2:1096, where for some reason it does this
    ## Why?  No idea.
    return socket_obj
