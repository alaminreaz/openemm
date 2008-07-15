#!/usr/bin/env python
#	-*- python -*-
"""**********************************************************************************
*  The contents of this file are subject to the OpenEMM Public License Version 1.1
*  ("License"); You may not use this file except in compliance with the License.
*  You may obtain a copy of the License at http://www.agnitas.org/openemm.
*  Software distributed under the License is distributed on an "AS IS" basis,
*  WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License for
*  the specific language governing rights and limitations under the License.
* 
*  The Original Code is OpenEMM.
*  The Initial Developer of the Original Code is AGNITAS AG. Portions created by
*  AGNITAS AG are Copyright (C) 2006 AGNITAS AG. All Rights Reserved.
* 
*  All copies of the Covered Code must include on each user interface screen,
*  visible to all users at all times
*     (a) the OpenEMM logo in the upper left corner and
*     (b) the OpenEMM copyright notice at the very bottom center
*  See full license, exhibit B for requirements.
**********************************************************************************


"""
#
import	sys, os, signal, time, errno,socket
import	email.Message, email.Header
import	StringIO, codecs
import	agn
agn.require ('1.3.3')
agn.loglevel = agn.LV_INFO
#
delay = 180

configFilename = agn.base + os.sep + 'var' + os.sep + 'spool' + os.sep + 'bav' + os.sep + 'bav.conf'
localFilename = agn.base + os.sep + 'conf' + os.sep + 'bav' + os.sep + 'bav.conf-local'
arDirectory = agn.base + os.sep + 'var' + os.sep + 'spool' + os.sep + 'bav'
updateLog = agn.base + os.sep + 'var' + os.sep + 'run' + os.sep + 'bav-update.log'
mailBase = '/etc/mail'
#
charset = 'ISO-8859-1'
#charset = 'UTF-8'

def fileReader (fname):
	fd = open (fname, 'r')
	rc = [agn.chop (line) for line in fd.readlines () if not line[0] in '\n#']
	fd.close ()
	return rc

class Autoresponder:
	def __init__ (self, rid, timestamp, sender, subject, text, html):
		global	arDirectory

		self.rid = rid
		self.timestamp = timestamp
		self.sender = sender
		self.subject = subject
		self.text = self._encode (text)
		self.html = self._encode (html)
		self.fname = arDirectory + os.sep + 'ar_%s.mail' % rid
		self.limit = arDirectory + os.sep + 'ar_%s.limit' % rid

	def _encode (self, s):
		if s and charset != 'UTF-8':
			temp = StringIO.StringIO (s)
			convert = codecs.EncodedFile (temp, charset, 'UTF-8')
			s = convert.read ()
		return s

	def _mkheader (self, s):
		rc = ''
		for w in s.split ():
			needEncode = False
			for c in w:
				if ord (c) > 127:
					needEncode = True
					break
			if rc:
				rc += ' '
			if needEncode:
				h = email.Header.Header (w, charset)
				rc += h.encode ()
			else:
				rc += w
		return rc
	
	def _prepmsg (self, m, isroot, type, pl):
		m.set_charset (charset)
		m.set_type (type)
		if not isroot:
			del m['mime-version']
		m.set_payload (pl)

	def writeFile (self):
		msg = email.Message.Message ()
		if self.sender:
			msg['From'] = self._mkheader (self.sender)
		if self.subject:
			msg['Subject'] = self._mkheader (self.subject)
		if not self.html:
			self._prepmsg (msg, True, 'text/plain', self.text)
		else:
			text = email.Message.Message ()
			html = email.Message.Message ()
			self._prepmsg (text, False, 'text/plain', self.text)
			self._prepmsg (html, False, 'text/html', self.html)
			msg.set_type ('multipart/alternative')
			msg.attach (text)
			msg.attach (html)
		try:
			fd = open (self.fname, 'w')
			fd.write (msg.as_string (False) + '\n')
			fd.close ()
		except IOError, e:
			agn.log (agn.LV_ERROR, 'auto', 'Unable to write message %s %s' % (self.fname, `e.args`))
	
	def removeFile (self):
		try:
			os.unlink (self.fname)
		except OSError, e:
			agn.log (agn.LV_ERROR, 'auto', 'Unable to remove file %s %s' % (self.fname, `e.args`))
		try:
			os.unlink (self.limit)
		except OSError:
			pass
#
class Data:
	def __init__ (self):
		global	arDirectory, updateLog

		fixdomain = 'localhost'
		self.domains = []
		self.last = ''
		self.autoresponder = []
		mtdom = {}
		try:
			for line in fileReader (mailBase + '/mailertable'):
				parts = line.split ()
				if len (parts) > 0 and parts[0][0] != '.':
					self.domains.append (parts[0])
					mtdom[parts[0]] = 1
		except IOError, e:
			agn.log (agn.LV_ERROR, 'data', 'Unable to read mailertable %s' % `e.args`)
		try:
			for line in fileReader (mailBase + '/relay-domains'):
				if mtdom.has_key (line):
					mtdom[line] += 1
				else:
					agn.log (agn.LV_ERROR, 'data', 'We relay domain "%s" without catching it in mailertable' % line)
			for key in mtdom.keys ():
				if mtdom[key] == 1:
					agn.log (agn.LV_ERROR, 'data', 'We define domain "%s" in mailertable, but do not relay it' % key)
		except IOError, e:
			agn.log (agn.LV_ERROR, 'data', 'Unable to read relay-domains %s' % `e.args`)

		if not self.domains:
			self.domains.append (fixdomain)
		try:
			files = os.listdir (arDirectory)
			for file in files:
				if len (file) > 8 and file[:3] == 'ar_' and file[-5:] == '.mail':
					rid = file[3:-5]
					self.autoresponder.append (Autoresponder (rid, 0, None, None, None, None))
		except OSError, e:
			agn.log (agn.LV_ERROR, 'data', 'Unable to read directory %s %s' % (arDirectory, `e.args`))
		self.updateCount = 0
	
	def removeUpdateLog (self):
		try:
			os.unlink (updateLog)
		except OSError, e:
			if e.args[0] != errno.ENOENT:
				agn.log (agn.LV_ERROR, 'data', 'Failed to remove old update log %s %s' % (updateLog, `e.args`))
		
	def done (self):
		self.removeUpdateLog ()

	def readMailFiles (self):
		rc = ''
		try:
			for line in fileReader (mailBase + '/local-host-names'):
				rc += '@%s\taccept:rid=local\n' % line
		except IOError, e:
			agn.log (agn.LV_ERROR, 'data', 'Unable to read local-host-names %s' % `e.args`)
		try:
			lhost = socket.getfqdn ()
			if lhost:
				rc += '@%s\taccept:rid=local\n' % lhost
		except Exception, e:
			agn.log (agn.LV_ERROR, 'data', 'Unable to find local FQDN %s' % `e.args`)
		try:
			for line in fileReader (mailBase + '/virtusertable'):
				parts = line.split ()
				if len (parts) == 2:
					rc += '%s\taccept:rid=virt,fwd=%s\n' % (parts[0], parts[1])
		except IOError, e:
			agn.log (agn.LV_ERROR, 'data', 'Unable to read virtusertable %s' % `e.args`)
		return rc
	def readDatabase (self, auto):
		rc = ''
		db = agn.DBase ()
		if not db:
			agn.log (agn.LV_ERROR, 'data', 'Unable to create database connection')
			raise agn.error ('readDatabase.open')
		try:
			i = db.newInstance ()
			if not i:
				agn.log (agn.LV_ERROR, 'data', 'Unable to get database cursor')
				raise agn.error ('readDatabase.cursor')
			try:


				query = 'SELECT rid, company_id, forward_enable, forward, ar_enable, ar_sender, ar_subject, ar_text, ar_html, date_format(change_date,\'%Y%m%d%H%i%S\') FROM mailloop_tbl'
				if not i.queryStart (query):
					agn.log (agn.LV_ERROR, 'data', 'Unable to setup database query ' + query)
					raise agn.error ('readDatabase.query')
				while 1:
					(st, record) = i.queryNext ()
					if not st:
						agn.log (agn.LV_ERROR, 'data', 'Failed to read next record')
						raise agn.error ('readDataBase.nextRecord')
					if not record:
						break
					(rid, company_id, forward_enable, forward, ar_enable, ar_sender, ar_subject, ar_text, ar_html, timestamp) = record
					aliases = None
					if not rid is None:
						rid = str (rid)

						timestamp = int (timestamp)
						if ar_enable and not ar_text:
							ar_enable = False
						if ar_enable:
							auto.append (Autoresponder (rid, timestamp, ar_sender, ar_subject, ar_text, ar_html))
						for domain in self.domains:
							line = 'ext_%s@%s\taccept:rid=%s' % (rid, domain, rid)
							if company_id:
								line += ',cid=%d' % company_id
							if forward_enable and forward:
								line += ',fwd=%s' % forward
							if ar_enable:
								line += ',ar=%s' % rid
							agn.log (agn.LV_VERBOSE, 'data', 'Add line: ' + line)
							rc += line + '\n'
						if aliases and self.domains:
							for alias in aliases.split ():
								rc += '%s\talias=ext_%s@%s\n' % (alias, rid, self.domains[0])
			finally:
				i.close ()
		finally:
			db.close ()
		return rc
	
	def readLocalFiles (self):
		rc = ''
		try:
			for line in fileReader (localFilename):
				rc += line + '\n'
		except IOError:
			pass
		return rc
	
	def updateAutoresponder (self, auto):
		newlist = []
		for new in auto:
			found = None
			for old in self.autoresponder:
				if new.rid == old.rid:
					found = old
					break
			if not found or new.timestamp > found.timestamp:
				new.writeFile ()
				newlist.append (new)
			else:
				newlist.append (old)
		for old in self.autoresponder:
			found = False
			for new in newlist:
				if old.rid == new.rid:
					found = True
					break
			if not found:
				old.removeFile ()
		self.autoresponder = newlist
	
	def renameFile (self, oldFile, newFile):
		try:
			os.rename (oldFile, newFile)
		except OSError, e:
			agn.log (agn.LV_ERROR, 'data', 'Unable to rename %s to %s %s' % (oldFile, newFile, `e.args`))
			try:
				os.unlink (oldFile)
			except OSError, e:
				agn.log (agn.LV_WARNING, 'data', 'Failed to remove temp. file %s %s' % (oldFile, `e.args`))
			raise agn.error ('renameFile')

	def updateConfigfile (self, new):
		global	configFilename 

		if new != self.last:
			temp = configFilename + '.%d' % os.getpid ()
			try:
				fd = open (temp, 'w')
				fd.write (new)
				fd.close ()
				self.renameFile (temp, configFilename)
			except IOError, e:
				agn.log (agn.LV_ERROR, 'data', 'Unable to write %s %s' % (temp, `e.args`))
				raise agn.error ('updateConfigfile.open')

	def writeUpdateLog (self, text):
		global	updateLog
		
		try:
			fd = open (updateLog, 'a')
			fd.write ('%d %s\n' % (self.updateCount, text))
			fd.close ()
			self.updateCount += 1
		except IOError, e:
			agn.log (agn.LV_ERROR, 'data', 'Unable to write update log %s %s' % (updateLog, `e.args`))

	def update (self, forced):
		try:
			auto = []
			new = self.readMailFiles ()
			new += self.readDatabase (auto)
			new += self.readLocalFiles ()
			self.updateAutoresponder (auto)
			self.updateConfigfile (new)
			updateText = 'success'
		except agn.error, e:
			agn.log (agn.LV_ERROR, 'data', 'Update failed: ' + e.msg)
			updateText = 'failed: ' + e.msg
		if forced:
			self.writeUpdateLog (updateText)
#
running = True
reread = True
def handler (sig, stack):
	global	running, reread
	
	if sig == signal.SIGUSR1:
		reread = True
	else:
		running = False

signal.signal (signal.SIGINT, handler)
signal.signal (signal.SIGTERM, handler)
signal.signal (signal.SIGUSR1, handler)
signal.signal (signal.SIGHUP, signal.SIG_IGN)

agn.log (agn.LV_INFO, 'main', 'Starting up')
agn.lock ()
data = Data ()
while running:
	forced = reread
	reread = False
	data.update (forced)
	n = delay
	while n > 0 and running and not reread:
		time.sleep (1)
		n -= 1
data.done ()
agn.unlock ()
agn.log (agn.LV_INFO, 'main', 'Going down')