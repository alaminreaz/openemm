#	-*- mode: python; mode: fold -*-
#
"""

**********************************************************************************
* The contents of this file are subject to the Common Public Attribution
* License Version 1.0 (the "License"); you may not use this file except in
* compliance with the License. You may obtain a copy of the License at
* http://www.openemm.org/cpal1.html. The License is based on the Mozilla
* Public License Version 1.1 but Sections 14 and 15 have been added to cover
* use of software over a computer network and provide for limited attribution
* for the Original Developer. In addition, Exhibit A has been modified to be
* consistent with Exhibit B.
* Software distributed under the License is distributed on an "AS IS" basis,
* WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
* the specific language governing rights and limitations under the License.
* 
* The Original Code is OpenEMM.
* The Original Developer is the Initial Developer.
* The Initial Developer of the Original Code is AGNITAS AG. All portions of
* the code written by AGNITAS AG are Copyright (c) 2007 AGNITAS AG. All Rights
* Reserved.
* 
* Contributor(s): AGNITAS AG. 
**********************************************************************************
Support routines for general and company specific purposes:
	class struct:     general empty class for temp. structured data
	class error:	  new version for general execption
	def chop:         removes trailing newlines
	def atob:         converts a string to a boolean value
	def numfmt:       converts a number to pretty printed version
	def validate:     validates an input string
	def filecount:    counts files matching a pattern in a directory
	def which:        finds program in path
	def mkpath:       creates a path from path components
	def fingerprint:  calculates a fingerprint from a file
	def toutf8:       converts input string to UTF-8 encoding
	def fromutf8:     converts UTF-8 encoded strings to unicode
	def msgn:         output a message on stdout, if verbose ist set
	def msgcnt:       output a number for progress
	def msg:          output a message with trailing newline on stdout,
	                  if verbose is set
	def err:          output a message on stderr
	def transformSQLwildcard: transform a SQL wildcard string to a regexp
	def compileSQLwildcard: transform and compile a SQL wildcard
	class UserStatus: describes available user stati

	class Backlog:    support class for enabling backlogging
	def level_name:   returns a string representation of a log level
	def logfilename:  creates the filename to write logfiles to
	def logappend:    copies directly to logfile
	def log:          writes an entry to the logfile
	def mark:         writes a mark to the logfile, if nothing had been
	                  written for a descent time
	def backlogEnable: switch backlogging on
	def backlogDisable: switch backlogging off
	def backlogRestart: flush all recorded entries and restart with
	                    a clean buffer
	def backlogSuspend: suspend storing entries to backlog
	def backlogResume: resume storing entries to backlog
	def backlogSave:  write current backlog to logfile

	def lock:         creates a lock for this running process
	def unlock:       removes the lock
	def signallock:   send signal to process owing a lockfile

	class Filepos:    line by line file reading with remembering th
	                  the file position
	
	def die:          terminate the program removing aquired lock, if
	                  neccessary
	rip = die         alias for die
	
	def mailsend:     send a mail using SMTP
	class UID:         handles parsing and validation of UIDs

	class DBCursor:    a cursor instance for database access
	class DBase:       an interface to the database
	
	class Datasource:  easier handling for datasource IDs
	class Template:    simple templating system

"""
#
# Imports, Constants and global Variables
#{{{
import	sys, os, types, errno, stat, signal
import	time, re, socket, md5, sha
import	platform, traceback, codecs
import	smtplib
try:

	import	MySQLdb
	database = MySQLdb
except ImportError:
	database = None
#
changelog = [
	('2.0.0', '2008-04-18', 'Initial version of redesigned code', 'ud@agnitas.de'),
	('2.0.1', '2008-07-01', 'Added autocommitment', 'ud@agnitas.de'),
	('2.0.3', '2008-07-31', 'Template with inclusing support', 'ud@agnitas.de'),
	('2.0.4', '2008-08-07', 'Added numfmt', 'ud@agnitas.de'),
	('2.0.5', '2008-08-11', 'Added validate', 'ud@agnitas.de'),
]
version = (changelog[-1][0], '2008-08-21 16:03:52 CEST', 'ud')
#
verbose = 1
system = platform.system ().lower ()
host = platform.node ()
if host.find ('.') != -1:
	host = host.split ('.')[0]

if system == 'windows':
	import	_winreg
	
	def winregFind (key, qkey):
		try:
			value = None
			rkey = _winreg.OpenKey (_winreg.HKEY_LOCAL_MACHINE, key)
			found = True
			n = 0
			while value is None:
				temp = _winreg.EnumValue (rkey, n)
				if qkey is None or qkey == temp[0]:
					value = temp[1]
				n += 1
			rkey.Close ()
		except WindowsError:
			value = None
		return value

	pythonbin = winregFind (r'SOFTWARE\Classes\Python.File\shell\open\command', None)
	if pythonbin is None:
		pythonbin = r'C:\Python25\python.exe'
	else:
		pythonbin = pythonbin.split ()[0]
		if len (pythonbin) > 1 and pythonbin[0] == '"' and pythonbin[-1] == '"':
			pythonbin = pythonbin[1:-1]
	pythonpath = os.path.dirname (pythonbin)
	try:
		home = os.environ['HOMEDRIVE'] + '\\OpenEMM'
	except KeyError:
		home = 'C:\\OpenEMM'
	os.environ['HOME'] = home
	iswin = True
	
	winstopfile = home + os.path.sep + 'var' + os.path.sep + 'run' + os.path.sep + 'openemm.stop'
	def winstop ():
		return os.path.isfile (winstopfile)
else:
	iswin = False
#
try:
	base = os.environ['HOME']
except KeyError:
	base = '.'

scripts = base + os.path.sep + 'bin' + os.path.sep + 'scripts'
if not scripts in sys.path:
	sys.path.insert (0, scripts)
#}}}
#
# Support routines
#{{{
class struct:
	"""class struct:

General empty class as placeholder for temp. structured data"""
	pass

class error (Exception):
	"""class error (Exception):

This is a general exception thrown by this module."""
	def __init__ (self, message = None):
		Exception.__init__ (self, message)
		self.msg = message

def require (checkversion, checklicence = None):
	if cmp (checkversion, version[0]) > 0:
		raise error ('Version too low, require at least %s, found %s' % (checkversion, version[0]))
	if checkversion.split ('.')[0] != version[0].split ('.')[0]:
		raise error ('Majoir version mismatch, %s is required, %s is available' % (checkversion.split ('.')[0], version[0].split ('.')[0]))
	if not checklicence is None and checklicence != licence:
		raise error ('Licence mismatch, require %d, but having %d' % (checklicence, licence))
		
def chop (s):
	"""def chop (s):

removes any trailing LFs and CRs."""
	while len (s) > 0 and s[-1] in '\r\n':
		s = s[:-1]
	return s

def atob (s):
	"""def atob (s):

tries to interpret the incoming string as a boolean value."""
	if s and len (s) > 0 and s[0] in [ '1', 'T', 't', 'Y', 'y', '+' ]:
		return True
	return False

def numfmt (n, separator = '.'):
	"""def numfmt (n, separator = '.'):

convert the number to a more readble form using separator."""
	if n == 0:
		return '0'
	if n < 0:
		prefix = '-'
		n = -n
	else:
		prefix = ''
	rc = ''
	while n > 0:
		if n >= 1000:
			rc = '%s%03d%s' % (separator, n % 1000, rc)
		else:
			rc = '%d%s' % (n, rc)
		n /= 1000
	return prefix + rc

def validate (s, pattern, *funcs, **kw):
	"""def validate (s, pattern *funcs):

pattern is a regular expression where s is matched against.
Each group element is validated against a function found in funcs."""
	if not pattern.startswith ('^'):
		pattern = '^' + pattern
	if not pattern.endswith ('$') or pattern.endswith ('\\$'):
		pattern += '$'
	try:
		reflags = kw['flags']
	except KeyError:
		reflags = 0
	try:
		pat = re.compile (pattern, reflags)
	except Exception, e:
		raise error ('Failed to compile regular expression "%s": %s' % (pattern, e.args[0]))
	mtch = pat.match (s)
	if mtch is None:
		raise error ('No match')
	if len (funcs) > 0:
		flen = len (funcs)
		n = 0
		report = []
		grps = mtch.groups ()
		if not grps:
			grps = [mtch.group ()]
		for elem in grps:
			if n < flen:
				if type (funcs[n]) in (types.ListType, types.TupleType):
					(func, reason) = funcs[n]
				else:
					func = funcs[n]
					reason = '%r' % func
				if not func (elem):
					report.append ('Failed in group #%d: %s' % (n + 1, reason))
			n += 1
		if report:
			raise error ('Validation failed: %s' % ', '.join (report))

def filecount (directory, pattern):
	"""def filecount (directory, pattern):

counts the files in dir which are matching the regular expression
in pattern."""
	pat = re.compile (pattern)
	dirlist = os.listdir (directory)
	count = 0
	for fname in dirlist:
		if pat.search (fname):
			count += 1
	return count

def which (program):
	"""def which (program):

finds 'program' in the $PATH enviroment, returns None, if not available."""
	rc = None
	try:
		paths = os.environ['PATH'].split (':')
	except KeyError:
		paths = []
	for path in paths:
		if path:
			p = path + os.path.sep + program
		else:
			p = program
		if os.access (p, os.X_OK):
			rc = p
			break
	return rc

def mkpath (*parts, **opts):
	"""def mkpath (*parts, **opts):

create a valid pathname from the elements"""
	try:
		absolute = opts['absolute']
	except KeyError:
		absolute = False
	rc = os.path.sep.join (parts)
	if absolute and not rc.startswith (os.path.sep):
		rc = os.path.sep + rc

	if iswin:
		try:
			drive = opts['drive']
			if len (drive) == 1:
				rc += drive + ':' + rc
		except KeyError:
			pass
	return os.path.normpath (rc)

def fingerprint (fname):
	"""def fingerprint (fname):

calculates a MD5 hashvalue (a fingerprint) of a given file."""
	fp = md5.new ()
	fd = open (fname, 'r')
	while 1:
		chunk = fd.read (65536)
		if chunk == '':
			break
		fp.update (chunk)
	fd.close ()
	return fp.hexdigest ()

__encoder = codecs.getencoder ('UTF-8')
def toutf8 (s, charset = 'ISO-8859-1'):
	"""def toutf8 (s, [charset]):

convert unicode (or string with charset information) inputstring
to UTF-8 string."""
	if type (s) == types.StringType:
		s = unicode (s, charset)
	return __encoder (s)[0]
def fromutf8 (s):
	"""def fromutf8 (s):

converts an UTF-8 coded string to a unicode string."""
	return unicode (s, 'UTF-8')

def msgn (s):
	"""def msgn (s):

prints s to stdout, if the module variable verbose is not equal to 0."""
	global	verbose

	if verbose:
		sys.stdout.write (s)
		sys.stdout.flush ()
def msgcnt (cnt):
	"""def msgcnt (cnt):

prints a counter to stdout. If the number has more than eight digits, this
function will fail. msgn() is used for the output itself."""
	msgn ('%8d\b\b\b\b\b\b\b\b' % cnt)
def msg (s):
	"""def msg (s):

prints s with a newline appended to stdout. msgn() is used for the output
itself."""
	msgn (s + '\n')
def err (s):
	"""def err (s):

prints s with a newline appended to stderr."""
	sys.stderr.write (s + '\n')
	sys.stderr.flush ()

def transformSQLwildcard (s):
	r = ''
	needFinal = True
	for ch in s:
		needFinal = True
		if ch in '$^*?()+[{]}|\\.':
			r += '\\%s' % ch
		elif ch == '%':
			r += '.*'
			needFinal = False
		elif ch == '_':
			r += '.'
		else:
			r += ch
	if needFinal:
		r += '$'
	return r
def compileSQLwildcard (s, reFlags = 0):
	return re.compile (transformSQLwildcard (s), reFlags)

class UserStatus:
	UNSET = 0
	ACTIVE = 1
	BOUNCE = 2
	ADMOUT = 3
	OPTOUT = 4
	WAITCONFIRM = 5
	BLACKLIST = 6
	SUSPEND = 7
	stati = { 'unset': UNSET,
		  'active': ACTIVE,
		  'bounce': BOUNCE,
		  'admout': ADMOUT,
		  'optout': OPTOUT,
		  'waitconfirm': WAITCONFIRM,
		  'blacklist': BLACKLIST,
		  'suspend': SUSPEND
		}
	rstati = None
	
	def __init__ (self):
		if self.rstati is None:
			self.rstati = {}
			for (var, val) in self.stati.items ():
				self.rstati[val] = var
	
	def findStatus (self, st, dflt = None):
		rc = None
		if type (st) in types.StringTypes:
			try:
				rc = self.stati[st]
			except KeyError:
				rc = None
		if rc is None:
			try:
				rc = int (st)
			except ValueError:
				rc = None
		if rc is None:
			rc = dflt
		return rc
	
	def findStatusName (self, stid):
		try:
			rc = self.rstati[stid]
		except KeyError:
			rc = None
		return rc
#}}}
#
# 1.) Logging
#
#{{{
class Backlog:
	def __init__ (self, maxcount, level):
		self.maxcount = maxcount
		self.level = level
		self.backlog = []
		self.count = 0
		self.isSuspended = False
		self.asave = None
	
	def add (self, s):
		if not self.isSuspended and self.maxcount:
			if self.maxcount > 0 and self.count >= self.maxcount:
				self.backlog.pop (0)
			else:
				self.count += 1
			self.backlog.append (s)
	
	def suspend (self):
		self.isSuspended = True
	
	def resume (self):
		self.isSuspended = False
	
	def restart (self):
		self.backlog = []
		self.count = 0
		self.isSuspended = False
	
	def save (self):
		if self.count > 0:
			self.backlog.insert (0, '-------------------- BEGIN BACKLOG --------------------\n')
			self.backlog.append ('--------------------  END BACKLOG  --------------------\n')
			logappend (self.backlog)
			self.backlog = []
			self.count = 0
	
	def autosave (self, level):
		if not self.asave is None and level in self.asave:
			return True
		return False
	
	def addLevelForAutosave (self, level):
		if self.asave is None:
			self.asave = [level]
		elif not level in self.asave:
			self.asave.append (level)
	
	def removeLevelForAutosave (self, level):
		if not self.asave is None and level in self.asave:
			self.asave.remove (level)
			if not self.asave:
				self.asave = None
	
	def clearLevelForAutosave (self):
		self.asave = None
	
	def setLevelForAutosave (self, levels):
		if levels:
			self.asave = levels
		else:
			self.asave = None

LV_NONE = 0
LV_FATAL = 1
LV_REPORT = 2
LV_ERROR = 3
LV_WARNING = 4
LV_NOTICE = 5
LV_INFO = 6
LV_VERBOSE = 7
LV_DEBUG = 8
loglevel = LV_WARNING
loghost = host
logname = None
logpath = None
outlevel = LV_FATAL
outstream = None
backlog = None
try:
	logpath = os.environ['LOG_HOME']
except KeyError:
	try:
		logpath = os.environ['HOME'] + os.path.sep + 'var' + os.path.sep + 'log'
	except KeyError:
		logpath = 'var' + os.path.sep + 'log'
if len (sys.argv) > 0:
	logname = os.path.basename (sys.argv[0])
	(basename, extension) = os.path.splitext (logname)
	if extension.lower () == '.py':
		logname = basename
if not logname:
	logname = 'unset'
loglast = 0
#
def level_name (lvl):
	"""def level_name (lvl):

returns a name for a numeric loglevel."""
	if lvl == LV_FATAL:
		name = 'FATAL'
	elif lvl == LV_REPORT:
		name = 'REPORT'
	elif lvl == LV_ERROR:
		name = 'ERROR'
	elif lvl == LV_WARNING:
		name = 'WARNING'
	elif lvl == LV_NOTICE:
		name = 'NOTICE'
	elif lvl == LV_INFO:
		name = 'INFO'
	elif lvl == LV_VERBOSE:
		name = 'VERBOSE'
	elif lvl == LV_DEBUG:
		name = 'DEBUG'
	else:
		name = str (lvl)
	return name

def logfilename ():
	global	logpath, loghost, logname
	
	now = time.localtime (time.time ())
	return '%s%s%04d%02d%02d-%s-%s.log' % (logpath, os.path.sep, now[0], now[1], now[2], loghost, logname)

def logappend (s):
	global	loglast

	fname = logfilename ()
	try:
		fd = open (fname, 'a')
		if type (s) in types.StringTypes:
			fd.write (s)
		elif type (s) in (types.ListType, types.TupleType):
			for l in s:
				fd.write (l)
		else:
			fd.write (str (s) + '\n')
		fd.close ()
		loglast = int (time.time ())
	except Exception, e:
		err ('LOGFILE write failed[%s, %s]: %s' % (`type (e)`, `e.args`, `s`))

def log (lvl, ident, s):
	global	loglevel, logname, backlog

	if not backlog is None and backlog.autosave (lvl):
		backlog.save ()
		backlogIgnore = True
	else:
		backlogIgnore = False
	if lvl <= loglevel or \
	   (lvl <= outlevel and not outstream is None) or \
	   (not backlog is None and lvl <= backlog.level):
		if not ident:
			ident = logname
		now = time.localtime (time.time ())
		lstr = '[%02d.%02d.%04d  %02d:%02d:%02d] %d %s/%s: %s\n' % (now[2], now[1], now[0], now[3], now[4], now[5], os.getpid (), level_name (lvl), ident, s)
		if lvl <= loglevel:
			logappend (lstr)
		else:
			backlogIgnore = False
		if lvl <= outlevel and not outstream is None:
			outstream.write (lstr)
			outstream.flush ()
		if not backlogIgnore and not backlog is None and lvl <= backlog.level:
			backlog.add (lstr)

def mark (lvl, ident, dur = 60):
	global	loglast
	
	now = int (time.time ())
	if loglast + dur * 60 < now:
		log (lvl, ident, '-- MARK --')

def backlogEnable (maxcount = 100, level = LV_DEBUG):
	global	backlog
	
	if maxcount == 0:
		backlog = None
	else:
		backlog = Backlog (maxcount, level)

def backlogDisable ():
	global	backlog
	
	backlog = None

def backlogRestart ():
	global	backlog
	
	if not backlog is None:
		backlog.restart ()

def backlogSave ():
	global	backlog
	
	if not backlog is None:
		backlog.save ()

def backlogSuspend ():
	global	backlog
	
	if not backlog is None:
		backlog.suspend ()

def backlogResume ():
	global	backlog
	
	if not backlog is None:
		backlog.resume ()

def logExcept (typ, value, tb):
	ep = traceback.format_exception (typ, value, tb)
	rc = 'CAUGHT EXCEPTION:\n'
	for p in ep:
		rc += p
	backlogSave ()
	log (LV_FATAL, 'except', rc)
	err (rc)
sys.excepthook = logExcept
#}}}
#
# 2.) Locking
#
#{{{

if iswin:
	lockfd = None
lockname = None
try:
	lockpath = os.environ['LOCK_HOME']
except KeyError:
	try:
		lockpath = os.environ['HOME'] + os.path.sep + 'var' + os.path.sep + 'lock'
	except KeyError:
		lockpath = 'var' + os.path.sep + 'lock'

def _mklockpath (pgmname):
	global	lockpath
	
	return lockpath + os.path.sep + pgmname + '.lock'

def lock (isFatal = True):
	global	lockname, logname

	if lockname:
		return lockname
	name = _mklockpath (logname)
	s = '%10d\n' % (os.getpid ())
	report = 'Try locking using file "' + name + '"\n'
	n = 0
	while n < 2:
		n += 1
		try:
			if not lockname:
				fd = os.open (name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0444)
				os.write (fd, s)
				os.close (fd)
				lockname = name

				if iswin:
					global	lockfd

					lockfd = open (lockname)
					os.chmod (lockname, 0777)
				report += 'Lock aquired\n'
		except OSError, e:
			if e.errno == errno.EEXIST:
				report += 'File exists, try to read it\n'
				try:
					fd = os.open (name, os.O_RDONLY)
					inp = os.read (fd, 32)
					os.close (fd)
					idx = inp.find ('\n')
					if idx != -1:
						inp = inp[:idx]
					inp = chop (inp)
					pid = int (inp)
					if pid > 0:
						report += 'Locked by process %d, look if it is still running\n' % (pid)
						try:

							if iswin:
								try:
									os.unlink (name)
									n -= 1
								except WindowsError:
									pass
							else:
								os.kill (pid, 0)
							report += 'Process is still running\n'
							n += 1
						except OSError, e:
							if e.errno == errno.ESRCH:
								report += 'Remove stale lockfile\n'
								try:
									os.unlink (name)
								except OSError, e:
									report += 'Unable to remove lockfile: ' + e.strerror + '\n'
							elif e.errno == errno.EPERM:
								report += 'Process is running and we cannot access it\n'
							else:
								report += 'Unable to check: ' + e.strerror + '\n'
				except OSError, e:
					report += 'Unable to read file: ' + e.strerror + '\n'
			else:
				report += 'Unable to create file: ' + e.strerror + '\n'
	if not lockname and isFatal:
		raise error (report)
	return lockname

def unlock ():
	global	lockname

	if lockname:
		try:

			if iswin:
				global	lockfd

				if not lockfd is None:
					lockfd.close ()
					lockfd = None
				os.chmod (lockname, 0777)
			os.unlink (lockname)
			lockname = None
		except OSError, e:
			if e.errno != errno.ENOENT:
				raise error ('Unable to remove lock: ' + e.strerror + '\n')

def signallock (program, signr = signal.SIGTERM):
	rc = False
	report = ''
	fname = _mklockpath (program)
	try:
		fd = open (fname, 'r')
		pline = fd.readline ()
		fd.close ()
		try:
			pid = int (pline.strip ())
			if pid > 0:
				try:
					os.kill (pid, signr)
					rc = True
					report = None
				except OSError, e:
					if e.errno == errno.ESRCH:
						report += 'Process %d does not exist\n' % pid
						try:
							os.unlink (fname)
						except OSError, e:
							report += 'Unable to remove stale lockfile %s %s\n' % (fname, `e.args`)
					elif e.errno == errno.EPERM:
						report += 'No permission to signal process %d\n' % pid
					else:
						report += 'Failed to signal process %d %s' % (pid, `e.args`)
			else:
				report += 'PIDFile contains invalid PID: %d\n' % pid
		except ValueError:
			report += 'Content of PIDfile is not valid: "%s"\n' % chop (pline)
	except IOError, e:
		if e.args[0] == errno.ENOENT:
			report += 'Lockfile %s does not exist\n' % fname
		else:
			report += 'Lockfile %s cannot be opened: %s\n' % (fname, `e.args`)
	return (rc, report)
#}}}
#
# 3.) file I/O
#
#{{{
archtab = {}
def mkArchiveDirectory (path, mode = 0777):
	global	archtab

	tt = time.localtime (time.time ())
	ts = '%04d%02d%02d' % (tt[0], tt[1], tt[2])
	arch = path + os.path.sep + ts
	if not archtab.has_key (arch):
		try:
			st = os.stat (arch)
			if not stat.S_ISDIR (st[stat.ST_MODE]):
				raise error ('%s is not a directory' % arch)
		except OSError, e:
			if e.args[0] != errno.ENOENT:
				raise error ('Unable to stat %s: %s' % (arch, e.args[1]))
			try:
				os.mkdir (arch, mode)
			except OSError, e:
				raise error ('Unable to create %s: %s' % (arch, e.args[1]))
		archtab[arch] = True
	return arch
	
seektab = []
class Filepos:
	def __stat (self, stat_file):
		try:
			if stat_file:
				st = os.stat (self.fname)
			else:
				st = os.fstat (self.fd.fileno ())
			rc = (st[stat.ST_INO], st[stat.ST_CTIME], st[stat.ST_SIZE])
		except (OSError, IOError):
			rc = None
		return rc

	def __open (self):
		global	seektab

		errmsg = None
		if os.access (self.info, os.F_OK):
			try:
				fd = open (self.info, 'r')
				line = fd.readline ()
				fd.close ()
				parts = chop (line).split (':')
				if len (parts) == 3:
					self.inode = int (parts[0])
					self.ctime = int (parts[1])
					self.pos = int (parts[2])
				else:
					errmsg = 'Invalid input for %s: %s' % (self.fname, line)
			except (IOError, ValueError), e:
				errmsg = 'Unable to read info file %s: %s' % (self.info, `e.args`)
		if not errmsg:
			try:
				self.fd = open (self.fname, 'r')
			except IOError, e:
				errmsg = 'Unable to open %s: %s' % (self.fname, `e.args`)
			if self.fd:
				st = self.__stat (False)
				if st:
					ninode = st[0]
					nctime = st[1]
					if ninode == self.inode:
						if st[2] >= self.pos:
							self.fd.seek (self.pos)
						else:
							self.pos = 0
					self.inode = ninode
					self.ctime = nctime
				else:
					errmsg = 'Failed to stat %s' % self.fname
				if errmsg:
					self.fd.close ()
					self.fd = None
		if errmsg:
			raise error (errmsg)
		if not self in seektab:
			seektab.append (self)

	def __init__ (self, fname, info, checkpoint = 64):
		self.fname = fname
		self.info = info
		self.checkpoint = checkpoint
		self.fd = None
		self.inode = -1
		self.ctime = 0
		self.pos = 0
		self.count = 0
		self.__open ()
	
	def __save (self):
		fd = open (self.info, 'w')
		fd.write ('%d:%d:%d' % (self.inode, self.ctime, self.fd.tell ()))
		fd.close ()
		self.count = 0
	
	def close (self):
		if self.fd:
			self.__save ()
			self.fd.close ()
			self.fd = None
		if self in seektab:
			seektab.remove (self)

	def __check (self):
		rc = True
		st = self.__stat (True)
		if st:
			if st[0] == self.inode and st[1] == self.ctime and st[2] > self.fd.tell ():
				rc = False
		return rc

	def __readline (self):
		line = self.fd.readline ()
		if line != '':
			self.count += 1
			if self.count >= self.checkpoint:
				self.__save ()
			return chop (line)
		else:
			return None
	
	def readline (self):
		line = self.__readline ()
		if line is None and not self.__check ():
			self.close ()
			self.__open ()
			line = self.__readline ()
		return line
#
def die (lvl = LV_FATAL, ident = None, s = None):
	global	seektab

	if s:
		err (s)
		log (lvl, ident, s)
	for st in seektab[:]:
		st.close ()
	unlock ()
	sys.exit (1)
rip = die
#}}}
#
# 4.) mailing/httpclient
#
#{{{
def mailsend (relay, sender, receivers, headers, body,
	      myself = host):
	def codetype (code):
		return code / 100
	rc = False
	if not relay:
		return (rc, 'Missing relay\n')
	if not sender:
		return (rc, 'Missing sender\n')
	if type (receivers) in types.StringTypes:
		receivers = [receivers]
	if len (receivers) == 0:
		return (rc, 'Missing receivers\n')
	if not body:
		return (rc, 'Empty body\n')
	report = ''
	try:
		s = smtplib.SMTP (relay)
		(code, detail) = s.helo (myself)
		if codetype (code) != 2:
			raise smtplib.SMTPResponseException (code, 'HELO ' + myself + ': ' + detail)
		else:
			report += 'HELO %s sent\n%d %s recvd\n' % (myself, code, detail)
		(code, detail) = s.mail (sender)
		if codetype (code) != 2:
			raise smtplib.SMTPResponseException (code, 'MAIL FROM:<' + sender + '>: ' + detail)
		else:
			report += 'MAIL FROM:<%s> sent\n%d %s recvd\n' % (sender, code, detail)
		for r in receivers:
			(code, detail) = s.rcpt (r)
			if codetype (code) != 2:
				raise smtplib.SMTPResponseException (code, 'RCPT TO:<' + r + '>: ' + detail)
			else:
				report += 'RCPT TO:<%s> sent\n%d %s recvd\n' % (r, code, detail)
		mail = ''
		hsend = False
		hrecv = False
		if headers:
			for h in headers:
				if len (h) > 0 and h[-1] != '\n':
					h += '\n'
				if not hsend and len (h) > 5 and h[:5].lower () == 'from:':
					hsend = True
				elif not hrecv and len (h) > 3 and h[:3].lower () == 'to:':
					hrecv = True
				mail = mail + h
		if not hsend:
			mail += 'From: ' + sender + '\n'
		if not hrecv:
			recvs = ''
			for r in receivers:
				if recvs:
					recvs += ', '
				recvs += r
			mail += 'To: ' + recvs + '\n'
		mail += '\n' + body
		(code, detail) = s.data (mail)
		if codetype (code) != 2:
			raise smtplib.SMTPResponseException (code, 'DATA: ' + detail)
		else:
			report += 'DATA sent\n%d %s recvd\n' % (code, detail)
		s.quit ()
		report += 'QUIT sent\n'
		rc = True
	except smtplib.SMTPConnectError, e:
		report += 'Unable to connect to %s, got %d %s response\n' % (relay, e.smtp_code, e.smtp_error)
	except smtplib.SMTPServerDisconnected:
		report += 'Server connection lost\n'
	except smtplib.SMTPResponseException, e:
		report += 'Invalid response: %d %s\n' % (e.smtp_code, e.smtp_error)
	except socket.error, e:
		report += 'General socket error: %s\n' % `e.args`
	except Exception, e:
		report += 'General problems during mail sending: %s, %s\n' % (`type (e)`, `e.args`)
	return (rc, report)
#}}}
#
# 5.) system interaction
#
#{{{


def fileAccess (path):
	if system != 'linux':
		raise error ('lsof only supported on linux')
	try:
		st = os.stat (path)
	except OSError, e:
		raise error ('failed to stat "%s": %s' % (path, `e.args`))
	device = st[stat.ST_DEV]
	inode = st[stat.ST_INO]
	rc = []
	fail = []
	seen = {}
	isnum = re.compile ('^[0-9]+$')
	for pid in [_p for _p in os.listdir ('/proc') if not isnum.match (_p) is None]:
		bpath = '/proc/%s' % pid
		checks = ['%s/%s' % (bpath, _c) for _c in 'cwd', 'exe', 'root']
		try:
			fdp = '%s/fd' % bpath
			for fds in os.listdir (fdp):
				checks.append ('%s/%s' % (fdp, fds))
		except OSError, e:
			fail.append ([e.args[0], '%s/fd: %s' % (bpath, e.args[1])])
		try:
			fd = open ('%s/maps' % bpath)
			for line in fd.readlines ():
				parts = line.split ()
				if len (parts) == 6 and parts[5].startswith ('/'):
					checks.append (parts[5].strip ())
			fd.close ()
		except IOError, e:
			fail.append ([e.args[0], '%s/maps: %s' % (bpath, e.args[1])])
		for check in checks:
			try:
				if seen[check]:
					rc.append (pid)
			except KeyError:
				seen[check] = False
				cpath = check
				try:
					fpath = None
					count = 0
					while fpath is None and count < 128 and cpath.startswith ('/'):
						count += 1
						st = os.lstat (cpath)
						if stat.S_ISLNK (st[stat.ST_MODE]):
							cpath = os.readlink (cpath)
						else:
							fpath = cpath
					if not fpath is None and st[stat.ST_DEV] == device and st[stat.ST_INO] == inode:
						rc.append (pid)
						seen[check] = True
				except OSError, e:
					fail.append ([e.args[0], '%s: %s' % (cpath, e.args[1])])
	return (rc, fail)
#}}}
#
# 6.) Validate UIDs
#
#{{{
class UID:
	def __init__ (self):
		self.companyID = 0
		self.mailingID = 0
		self.customerID = 0
		self.URLID = 0
		self.signature = None
		self.prefix = None
		self.password = None
	
	def __decodeBase36 (self, s):
		return int (s, 36)
	
	def __codeBase36 (self, i):
		if i == 0:
			return '0'
		elif i < 0:
			i = -i
			sign = '-'
		else:
			sign = ''
		s = ''
		while i > 0:
			s = '0123456789abcdefghijklmnopqrstuvwxyz'[i % 36] + s
			i /= 36
		return sign + s
	
	def __makeSignature (self, s):
		hashval = sha.sha (s).digest ()
		sig = ''
		for ch in hashval[::2]:
			sig += self.__codeBase36 ((ord (ch) >> 2) % 36)
		return sig
	
	def __makeBaseUID (self):
		if self.prefix:
			s = self.prefix + '.'
		else:
			s = ''
		s += self.__codeBase36 (self.companyID) + '.' + \
		     self.__codeBase36 (self.mailingID) + '.' + \
		     self.__codeBase36 (self.customerID) + '.' + \
		     self.__codeBase36 (self.URLID)
		return s
	
	def createSignature (self):
		return self.__makeSignature (self.__makeBaseUID () + '.' + self.password)
	
	def createUID (self):
		baseUID = self.__makeBaseUID ()
		return baseUID + '.' + self.__makeSignature (baseUID + '.' + self.password)
	
	def parseUID (self, uid):
		parts = uid.split ('.')
		plen = len (parts)
		if plen != 5 and plen != 6:
			raise error ('Invalid input format')
		start = plen - 5
		if plen == 6:
			self.prefix = parts[0]
		else:
			self.prefix = None
		try:
			self.companyID = self.__decodeBase36 (parts[start])
			self.mailingID = self.__decodeBase36 (parts[start + 1])
			self.customerID = self.__decodeBase36 (parts[start + 2])
			self.URLID = self.__decodeBase36 (parts[start + 3])
			self.signature = parts[start + 4]
		except ValueError:
			raise error ('Invalid input in data')
	
	def validateUID (self):
		lsig = self.createSignature ()
		return lsig == self.signature
#}}}
#
# 7.) General database interface
#
#{{{
if database:
	if database.apilevel != '2.0':
		err ('WARNING: Database API level is not 2.0, but ' + database.apilevel)

	if database.paramstyle != 'format':
		err ('WARNING: Database parameter style is not format, but ' + database.paramstyle)
	dbhost = 'localhost'
	dbuser = 'agnitas'
	dbpass = 'openemm'
	dbdatabase = 'openemm'

	class DBCache:
		def __init__ (self, data):
			self.data = data
			self.count = len (data)
			self.pos = 0
		
		def __iter__ (self):
			return self

		def next (self):
			if self.pos >= self.count:
				raise StopIteration ()
			record = self.data[self.pos]
			self.pos += 1
			return record

	class DBCursor:
		def __init__ (self, db, autocommit):
			self.db = db
			self.autocommit = autocommit
			self.curs = None
			self.desc = False
			self.rfparse = re.compile (':[A-Za-z0-9_]+|%')
			self.cache = {}
		
		def lastError (self):
			if self.db:
				return self.db.lastError ()
			return 'no database interface active'
		
		def close (self):
			if self.curs:
				try:
					self.curs.close ()
				except database.Error, e:
					if self.db:
						self.db.lasterr = e
				self.curs = None
				self.desc = False
	
		def __error (self, errmsg):
			if self.db:
				self.db.lasterr = errmsg
			self.close ()

		def open (self):
			self.close ()
			if self.db and self.db.isOpen ():
				try:
					self.curs = self.db.getCursor ()
				except database.Error, e:
					self.__error (e)
			if self.curs:
				return True
			return False
		
		def description (self):
			if self.desc:
				return self.curs.description
			return None


		def __reformat (self, req, parm):
			try:
				(nreq, varlist) = self.cache[req]
			except KeyError:
				nreq = ''
				varlist = []
				while 1:
					mtch = self.rfparse.search (req)
					if mtch is None:
						nreq += req
						break
					else:
						span = mtch.span ()
						nreq += req[:span[0]]
						if span[0] + 1 < span[1]:
							varlist.append (req[span[0] + 1:span[1]])
							nreq += '%s'
						else:
							nreq += '%%'
						req = req[span[1]:]
				self.cache[req] = (nreq, varlist)
			nparm = []
			for key in varlist:
				nparm.append (parm[key])
			return (nreq, nparm)

		def __valid (self):
			if not self.curs:
				if not self.open ():
					raise error ('Unable to setup cursor: ' + self.lastError ())
			
		def __iter__ (self):
			return self
		
		def next (self):
			try:
				data = self.curs.fetchone ()
			except database.Error, e:
				self.__error (e)
				raise error ('query next failed: ' + self.lastError ())
			if data is None:
				raise StopIteration ()
			return data

		def query (self, req, parm = None, cleanup = False):
			self.__valid ()
			try:
				if parm is None:
					self.curs.execute (req)
				else:

					(req, parm) = self.__reformat (req, parm)
					self.curs.execute (req, parm)
			except database.Error, e:
				self.__error (e)
				raise error ('query start failed: ' + self.lastError ())
			self.desc = True
			return self
		
		def queryc (self, req, parm = None, cleanup = False):
			if self.query (req, parm, cleanup) == self:
				try:
					data = self.curs.fetchall ()
					return DBCache (data)
				except database.Error, e:
					self.__error (e)
					raise error ('query all failed: ' + self.lastError ())
			raise error ('unable to setup query: ' + self.lastError ())
		
		def querys (self, req, parm = None, cleanup = False):
			rc = None
			for rec in self.query (req, parm, cleanup):
				rc = rec
				break
			return rc
		
		def sync (self, commit = True):
			rc = False
			if not self.db is None:
				if not self.db.db is None:
					try:
						if commit:
							self.db.db.commit ()
						else:
							self.db.db.rollback ()
						rc = True
					except database.Error, e:
						self.__error (e)
			return rc
		
		def update (self, req, parm = None, commit = False, cleanup = False):
			self.__valid ()
			try:
				if parm is None:
					self.curs.execute (req)
				else:

					(req, parm) = self.__reformat (req, parm)
					self.curs.execute (req, parm)
			except database.Error, e:
				self.__error (e)
				raise error ('update failed: ' + self.lastError ())
			rows = self.curs.rowcount
			if rows > 0 and (commit or self.autocommit):
				if not self.sync ():
					raise error ('commit failed: ' + self.lastError ())
			self.desc = False
			return rows
		execute = update

	class DBase:

		def __init__ (self, host = dbhost, user = dbuser, passwd = dbpass, database = dbdatabase):
			self.host = host
			self.user = user
			self.passwd = passwd
			self.database = database
			self.db = None
			self.lasterr = None

		def __error (self, errmsg):
			self.lasterr = errmsg
			self.close ()

		def lastError (self):
			if self.lasterr:

				return 'MySQL-%d: %s' % (self.lasterr.args[0], self.lasterr.args[1].strip ())
			if self.db is None:
				return 'No active database'
			return 'success'
			
		def commit (self):
			if self.db:
				self.db.commit ()
		
		def rollback (self):
			if self.db:
				self.db.rollback ()
		
		def close (self):
			if self.db:
				try:
					self.db.close ()
				except database.Error, e:
					self.lasterr = e
				self.db = None
	
		def open (self):
			self.close ()
			try:

				self.db = database.connect (self.host, self.user, self.passwd, self.database)
			except database.Error, e:
				self.__error (e)
			if self.db:
				return 1
			return 0
	
		def isOpen (self):
			if self.db:
				return 1
			return 0

                def getCursor (self):
			curs = None
			if not self.db:
				self.open ()
			if self.db:
				try:
					curs = self.db.cursor ()
					try:
						if curs.arraysize < 100:
							curs.arraysize = 100
					except AttributeError:
						pass
				except database.Error, err:
					self.__error (err)
			return curs

		def cursor (self, autocommit = False):
			c = None
			if not self.db:
				self.open ()
			if self.db:
				c = DBCursor (self, autocommit)
			return c
		
		def query (self, req):
			c = self.cursor ()
			if c:
				rc = None
				try:
					rc = [r for r in c.query (req)]
				finally:
					c.close ()
				return rc
			raise error ('Unable to get database cursor: ' + self.lastError ())
		
		def update (self, req):
			c = self.cursor ()
			if c:
				rc = None
				try:
					rc = c.update (req)
				finally:
					c.close ()
				return rc
			raise error ('Unable to get database cursor: ' + self.lastError ())
		execute = update
	
	class Datasource:
		def __init__ (self):
			self.cache = {}
		
		def getID (self, desc, companyID, sourceGroup, db = None):
			try:
				rc = self.cache[desc]
			except KeyError:
				rc = None
				if db is None:
					db = DBase ()
					dbOpened = True
				else:
					dbOpened = False
				if not db is None:
					curs = db.cursor ()
					if not curs is None:
						for state in [0, 1]:
							for rec in curs.query ('SELECT datasource_id FROM datasource_description_tbl WHERE company_id = %d AND description = :description' % companyID, {'description': desc}):
								rc = int (rec[0])
							if rc is None and state == 0:

								query = 'INSERT INTO datasource_description_tbl (description, company_id, sourcegroup_id, creation_date, change_date) VALUES ' + \
									'(:description, %d, %d, current_timestamp, current_timestamp)' % (companyID, sourceGroup)
								curs.update (query, {'description': desc}, commit = True)
						curs.close ()
					if dbOpened:
						db.close ()
				if not rc is None:
					self.cache[desc] = rc
			return rc
#}}}
#
# 8.) Simple templating
#
#{{{
class Template:
	"""class Template:

This class offers a simple templating system. One instance the class
using the template in string from. The syntax is inspirated by velocity,
but differs in serveral ways (and is even simpler). A template can start
with an optional code block surrounded by the tags '#code' and '#end'
followed by the content of the template. Access to variables and
expressions are realized by $... where ... is either a simple varibale
(e.g. $var) or something more complex, then the value must be
surrounded by curly brackets (e.g. ${var.strip ()}). To get a literal
'$'sign, just type it twice, so '$$' in the template leads into '$'
in the output. A trailing backslash removes the following newline to
join lines.

Control constructs must start in a separate line, leading whitespaces
ignoring, with a hash '#' sign. These constructs are supported and
are mostly transformed directly into a python construct:
	
## ...                      this introduces a comment up to end of line
#property(expr)             this sets a property of the template
#pragma(expr)               alias for property
#include(expr)              inclusion of file, subclass must realize this
#if(pyexpr)             --> if pyexpr:
#elif(pyexpr)           --> elif pyexpr:
#else                   --> else
#do(pycmd)              --> pycmd
#pass                   --> pass [same as #do(pass)]
#break			--> break [..]
#continue		--> continue [..]
#for(pyexpr)            --> for pyexpr:
#while(pyexpr)          --> while pyexpr:
#try                    --> try:
#except(pyexpr)         --> except pyexpr:
#finally                --> finally
#with(pyexpr)           --> with pyexpr:
#end                        ends an indention level
#stop                       ends processing of input template

To fill the template you call the method fill(self, namespace, lang = None)
where 'namespace' is a dictonary with names accessable by the template.
Beside, 'lang' could be set to a two letter string to post select language
specific lines from the text. These lines must start with a two letter
language ID followed by a colon, e.g.:
	
en:This is an example.
de:Dies ist ein Beispiel.

Depending on 'lang' only one (or none of these lines) are outputed. If lang
is not set, these lines are put (including the lang ID) both in the output.
If 'lang' is set, it is also copied to the namespace, so you can write the
above lines using the template language:

#if(lang=='en')
This is an example.
#elif(lang=='de')
Dies ist ein Beispiel.
#end

And for failsafe case, if lang is not set:

#try
 #if(lang=='en')
This is an example.
 #elif(lang=='de')
Dies ist ein Beispiel.
 #end
#except(NameError)
 #pass
#end
"""
	codeStart = re.compile ('^[ \t]*#code[^\n]*\n', re.IGNORECASE)
	codeEnd = re.compile ('(^|\n)[ \t]*#end[^\n]*(\n|$)', re.IGNORECASE | re.MULTILINE)
	token = re.compile ('((^|\n)[ \t]*#(#|property|pragma|include|if|elif|else|do|pass|break|continue|for|while|try|except|finally|with|end|stop)|\\$(\\$|[0-9a-z_]+(\\.[0-9a-z_]+)*|\\{[^}]*\\}))', re.IGNORECASE | re.MULTILINE)
	rplc = re.compile ('\\\\|"|\'|\n|\r|\t|\f|\v', re.MULTILINE)
	rplcMap = {'\n': '\\n', '\r': '\\r', '\t': '\\t', '\f': '\\f', '\v': '\\v'}
	langID = re.compile ('^([ \t]*)([a-z][a-z]):', re.IGNORECASE)
	def __init__ (self, content, precode = None, postcode = None):
		self.content = content
		self.precode = precode
		self.postcode = postcode
		self.compiled = None
		self.properties = {}
		self.namespace = None
		self.code = None
		self.indent = None
		self.empty = None
		self.compileErrors = None
	
	def __getitem__ (self, var):
		if not self.namespace is None:
			try:
				val = self.namespace[var]
			except KeyError:
				val = ''
		else:
			val = None
		return val
	
	def __setProperty (self, expr):
		try:
			(var, val) = [_e.strip () for _e in expr.split ('=', 1)]
			if len (val) >= 2 and val[0] in '"\'' and val[-1] == val[0]:
				quote = val[0]
				self.properties[var] = val[1:-1].replace ('\\%s' % quote, quote).replace ('\\\\', '\\')
			elif val.lower () in ('true', 'on', 'yes'):
				self.properties[var] = True
			elif val.lower () in ('false', 'off', 'no'):
				self.properties[var] = False
			else:
				try:
					self.properties[var] = int (val)
				except ValueError:
					self.properties[var] = val
		except ValueError:
			var = expr.strip ()
			if var:
				self.properties[var] = True
			
	def __indent (self):
		if self.indent:
			self.code += ' ' * self.indent
	
	def __code (self, code):
		self.__indent ()
		self.code += '%s\n' % code
		if code:
			if code[-1] == ':':
				self.empty = True
			else:
				self.empty = False
			
	def __deindent (self):
		if self.empty:
			self.__code ('pass')
		self.indent -= 1
	
	def __compileError (self, start, errtext):
		if not self.compileErrors:
			self.compileErrors = ''
		self.compileErrors += '** %s: %s ...\n\n\n' % (errtext, self.content[start:start + 60])

	def __replacer (self, mtch):
		rc = []
		for ch in mtch.group (0):
			try:
				rc.append (self.rplcMap[ch])
			except KeyError:
				rc.append ('\\x%02x' % ord (ch))
		return ''.join (rc)

	def __compileString (self, s):
		self.__code ('__result.append (\'%s\')' % re.sub (self.rplc, self.__replacer, s))
			
	def __compileExpr (self, s):
		self.__code ('__result.append (str (%s))' % s)

	def __compileCode (self, token, arg):
		if not token is None:
			if arg:
				self.__code ('%s %s:' % (token, arg))
			else:
				self.__code ('%s:' % token)
		elif arg:
			self.__code (arg)
					
	def __compileContent (self):
		self.code = ''
		if self.precode:
			self.code += self.precode
			if self.code[-1] != '\n':
				self.code += '\n'
		pos = 0
		clen = len (self.content)
		mtch = self.codeStart.search (self.content)
		if not mtch is None:
			start = mtch.end ()
			mtch = self.codeEnd.search (self.content, start)
			if not mtch is None:
				(end, pos) = mtch.span ()
				self.code += self.content[start:end] + '\n'
			else:
				self.__compileError (0, 'Unfinished code segment')
		self.indent = 0
		self.empty = False
		self.code += '__result = []\n'
		while pos < clen:
			mtch = self.token.search (self.content, pos)
			if mtch is None:
				start = clen
				end = clen
			else:
				(start, end) = mtch.span ()
				groups = mtch.groups ()
				if groups[1]:
					start += len (groups[1])
			if start > pos:
				self.__compileString (self.content[pos:start])
			pos = end
			if not mtch is None:
				tstart = start
				if not groups[2] is None:
					token = groups[2]
					arg = ''
					if token != '#':
						if pos < clen and self.content[pos] == '(':
							pos += 1
							level = 1
							quote = None
							escape = False
							start = pos
							end = -1
							while pos < clen and level > 0:
								ch = self.content[pos]
								if escape:
									escape = False
								elif ch == '\\':
									escape = True
								elif not quote is None:
									if ch == quote:
										quote = None
								elif ch in '\'"':
									quote = ch
								elif ch == '(':
									level += 1
								elif ch == ')':
									level -= 1
									if level == 0:
										end = pos
								pos += 1
							if start < end:
								arg = self.content[start:end]
							else:
								self.__compileError (tstart, 'Unfinished statement')
						if pos < clen and self.content[pos] == '\n':
							pos += 1
					if token == '#':
						while pos < clen and self.content[pos] != '\n':
							pos += 1
						if pos < clen:
							pos += 1
					elif token in ('property', 'pragma'):
						self.__setProperty (arg)
					elif token in ('include', ):
						try:
							included = self.include (arg)
							if included:
								self.content = self.content[:pos] + included + self.content[pos:]
						except error, e:
							self.__compileError (tstart, 'Failed to include "%s": %s' % (arg, e.msg))
					elif token in ('if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with'):
						if token in ('else', 'elif', 'except', 'finally'):
							if self.indent > 0:
								self.__deindent ()
							else:
								self.__compileError (tstart, 'Too many closeing blocks')
						if (arg and token in ('if', 'elif', 'for', 'while', 'except', 'with')) or \
						   (not arg and token in ('else', 'try', 'finally')):
							self.__compileCode (token, arg)
						elif arg:
							self.__compileError (tstart, 'Extra arguments for #%s detected' % token)
						else:
							self.__compileError (tstart, 'Missing statement for #%s' % token)
						self.indent += 1
					elif token in ('pass', 'break', 'continue'):
						if arg:
							self.__compileError (tstart, 'Extra arguments for #%s detected' % token)
						else:
							self.__compileCode (None, token)
					elif token in ('do', ):
						if arg:
							self.__compileCode (None, arg)
						else:
							self.__compileError (tstart, 'Missing code for #%s' % token)
					elif token in ('end', ):
						if arg:
							self.__compileError (tstart, 'Extra arguments for #end detected')
						if self.indent > 0:
							self.__deindent ()
						else:
							self.__compileError (tstart, 'Too many closing blocks')
					elif token in ('stop', ):
						pos = clen
				elif not groups[3] is None:
					expr = groups[3]
					if expr == '$':
						self.__compileString ('$')
					else:
						if len (expr) >= 2 and expr[0] == '{' and expr[-1] == '}':
							expr = expr[1:-1]
						self.__compileExpr (expr)
				elif not groups[0] is None:
					self.__compileString (groups[0])
		if self.indent > 0:
			self.__compileError (0, 'Missing %d closing #end statement(s)' % self.indent)
		if self.compileErrors is None:
			if self.postcode:
				if self.code and self.code[-1] != '\n':
					self.code += '\n'
				self.code += self.postcode
			self.compiled = compile (self.code, '<template>', 'exec')
	
	def include (self, arg):
		raise error ('Subclass responsible for implementing "include"')

	def property (self, var):
		try:
			return self.properties[var]
		except KeyError:
			return None

	def compile (self):
		if self.compiled is None:
			try:
				self.__compileContent ()
				if self.compiled is None:
					raise error ('Compilation failed: %s' % self.compileErrors)
			except Exception, e:
				raise error ('Failed to compile [%s] %s:\n%s\n' % (`type (e)`, `e.args`, self.code))

	def fill (self, namespace, lang = None):
		if self.compiled is None:
			self.compile ()
		if namespace is None:
			self.namespace = {}
		else:
			self.namespace = namespace.copy ()
		if not lang is None:
			self.namespace['lang'] = lang
		self.namespace['property'] = self.properties
		try:
			exec self.compiled in self.namespace
		except Exception, e:
			raise error ('Execution failed [%s]: %s' % (e.__class__.__name__, str (e)))
		result = ''.join (self.namespace['__result']).replace ('\\\n', '')
		if not lang is None:
			nresult = []
			for line in result.split ('\n'):
				mtch = self.langID.search (line)
				if mtch is None:
					nresult.append (line)
				else:
					(pre, lid) = mtch.groups ()
					if lid.lower () == lang:
						nresult.append (pre + line[mtch.end ():])
			result = '\n'.join (nresult)
		self.namespace['result'] = result
		return result
#}}}
