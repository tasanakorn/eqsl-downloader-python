#!/usr/bin/python
# coding=utf-8
import urllib
import urllib2
import re
import os
import ConfigParser

def adifFixup(rec):
    if rec.has_key('band') and not rec.has_key('band_rx'):
        rec['band_rx'] = rec['band']
    if rec.has_key('freq') and not rec.has_key('freq_rx'):
        rec['freq_rx'] = rec['freq']

def adiParse(adif_data):
    raw = adif_data
 
    # Find the EOH, in this simple example we are skipping
    # header parsing.
    pos = 0
    m = re.search('', raw, re.IGNORECASE)
    if m != None:
        # Start parsing our ADIF file after the  marker
        pos = m.end()
 
    recs = []
    rec = dict()
    while 1:
        # Find our next field definition &lt;...&gt;
        pos = raw.find('<', pos)
        if pos == -1:
             return recs
        endPos = raw.find('>', pos)
 
        # Split to get individual field elements out
        fieldDef = raw[pos + 1:endPos].split(':')
        fieldName = fieldDef[0].lower()
        if fieldName == 'eor':
            adifFixup(rec)     # fill in information from lookups
            recs.append(rec)   # append this record to our records list
            rec = dict()       # start a new record
 
            pos = endPos
        elif len(fieldDef) > 1:
            # We have a field definition with a length, get it's
            # length and then assign the value to the dictionary
            fieldLen = int(fieldDef[1])
            rec[fieldName] = raw[endPos + 1:endPos + fieldLen + 1]
        pos = endPos
    return recs


'''
	MAIN 
'''
BASE_URL = 'http://www.eqsl.cc'
MYCALL = ''
MYPASS = ''
USER_HOME = os.path.expanduser("~")
APP_CONFIG_DIR = USER_HOME + "/.eqslloader"
APP_CONFIG = APP_CONFIG_DIR + "/config"
DATA_DIR = USER_HOME + "/eqsl_card"
if (not os.path.isdir(APP_CONFIG_DIR)) :
    os.makedirs(APP_CONFIG_DIR)

config = ConfigParser.ConfigParser()
try:
    config.read(APP_CONFIG)
    MYCALL = config.get('GENERAL', 'MYCALL', MYCALL)
    MYPASS = config.get('GENERAL', 'MYPASS', MYPASS)
    DATA_DIR = config.get('GENERAL', 'DATA_DIR', DATA_DIR)
except:
    pass

if MYCALL == '' or MYPASS == '':
    print "Config folder = ", APP_CONFIG
    print "eQSL account information."
    MYCALL = raw_input("Callsign : ")
    MYPASS = raw_input("Password : ")
    print "Save config to ", APP_CONFIG
    config.add_section('GENERAL')
    config.set('GENERAL', 'MYCALL', MYCALL)
    config.set('GENERAL', 'MYPASS', MYPASS)
    config.set('GENERAL', 'DATA_DIR', DATA_DIR)
    config.write(open(APP_CONFIG, 'wb'))

if MYCALL == '' or MYPASS == '':
    exit()

print "Callsign = ", MYCALL

if (not os.path.isdir(DATA_DIR)) :
    os.makedirs(DATA_DIR)

url_opener = urllib2.build_opener( urllib2.HTTPHandler(debuglevel=0), urllib2.HTTPCookieProcessor() )
urllib2.install_opener(url_opener)

print "Login"
p = urllib.urlencode( { 'Callsign': MYCALL, 'EnteredPassword' : MYPASS, 'Login' : 'Go'} )
response = urllib2.urlopen(BASE_URL + '/qslcard/LoginFinish.cfm', p)
data = response.read()
print "List ADI file"
data = urllib2.urlopen(BASE_URL + '/qslcard/DownloadInBox.cfm').read()
m = re.search('<A HREF="(.*)">.ADI file</A>', data)
log_count = 0
card_download_count = 0
if m :
	adi_file = m.group(1)
	print adi_file
	print "Load ADI file"
	adif_data = urllib2.urlopen(BASE_URL + '/qslcard/' + adi_file).read()
	logs = adiParse(adif_data)
	for log in logs :
		log_count += 1
		output_file = DATA_DIR + '/' + log['qso_date'] + '-' + log['time_on'] + '-' + log['band'] + '-' + log['mode'] + '-' + log['call'].replace('/','-') + ".png"
		if (not os.path.isfile(output_file)) :
			card_url = '/qslcard/DisplayQSL.cfm?Callsign=' + log['call'] + '&VisitorCallsign=' + MYCALL + '&QSODate=' + log['qso_date'][0:4] + '-' + log['qso_date'][4:6] + '-' + log['qso_date'][6:8] + '%20' + log['time_on'][0:2] + ':' + log['time_on'][2:4] + ':00.0&Band=' + log['band'] + '&Mode=' + log['mode']
			card_html =  urllib2.urlopen(BASE_URL + card_url).read()
			m2 = re.search(' src="/CFFileServlet/_cf_image/([a-zA-Z0-9_\-.]*)"', card_html)
			if m2 :				
				card_image_url = "/CFFileServlet/_cf_image/" + m2.group(1)
				print "Load " + card_image_url + " -> " + output_file
				image_response = urllib2.urlopen(BASE_URL + card_image_url)
				local_file = open(output_file, "wb")
				local_file.write(image_response.read())
				local_file.close()
				card_download_count += 1
			else :
				print "Unable to find image"
else :	
	print "adi file not found"

print "Log = " + str(log_count)
print "Card download = " + str(card_download_count)