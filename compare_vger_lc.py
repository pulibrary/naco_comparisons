#!/usr/bin/env python
#-*- coding: utf-8 -*-
import argparse
import codecs
import ConfigParser
import csv
import cx_Oracle
import glob
import logging
import os
import subprocess
import sys
import time
import matplotlib.pyplot as plt
from matplotlib_venn import venn2
from pymarc import MARCReader

config = ConfigParser.RawConfigParser()
config.read('vger.cfg')
user = config.get('database', 'user')
pw = config.get('database', 'pw')
sid = config.get('database', 'sid')
ip = config.get('database', 'ip')

dsn_tns = cx_Oracle.makedsn(ip,1521,sid)
db = cx_Oracle.connect(user,pw,dsn_tns)

today = time.strftime('%Y%m%d')

cmarcedit='/opt/local/marcedit/cmarcedit.exe'
filename = './out/vger_auth_ids.csv'

LOG="./logs/"
OUTDIR="./out/"

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename=LOG+today+'.log',level=logging.INFO)

def main():
	'''
	main
	'''
	schema = ''
	vger_auth_ids = set()

	if voyager:
		get_vger_auth_ids()

	if names:
		schema = 'n'
	elif subjects:
		schema = 's'
	
	with open(filename,'r') as vgercsv:
		reader = csv.reader(vgercsv)
		for row in reader:
			lccn = row[1]
			if lccn.startswith(schema):
				vger_auth_ids.add(lccn.strip())

	idloc = read_dump(schema)
	v = vger_auth_ids # voyager lccns
	w = parse_ward(schema) # ward lccns
	vw = v.union(w) # ward plus voyager - this should be everything up-to-date
	vw_not_id = vw.difference(idloc)
	id_not_vw = idloc.difference(vw)
	
	with open(OUTDIR+schema+'_idloc_not_vgerward.csv','wb+') as iout:
		for lccn in id_not_vw:
			iout.write(lccn+'\n')

	with open(OUTDIR+schema+'_vgerward_not_idloc.csv','wb+') as vout:
		for lccn in vw_not_id:
			vout.write(lccn+'\n')

	# TODO: argparse schema
	logging.info('voyager ids in schema %s: %s' % (schema,len(vger_auth_ids)))
	logging.info('ward ids: %s' % len(w)) 
	logging.info('%s voyager + ward: %s' % (schema,len(vw)))
	logging.info('%s idloc: %s' % (schema,len(idloc)))
	logging.info('%s idloc not vger: %s' % (schema,len(id_not_vw)))
	logging.info('%s vger not idloc: %s' % (schema,len(vw_not_id)))

	make_venn(vw,idloc)


def parse_ward(schema):
	'''
	Remove Ward records that have been deleted or made obsolete 
	'''
	ward_dict = {}
	ward_lccns = set()

	for m in glob.glob(r'../../../Documents/working/authorities/unname1[89].[0-9][0-9]'):
		logging.info('opening %s' % m)
		marc = str(m)
		reader = MARCReader(file(marc))
		# try and if breaks (e.g. encoding errors in unname19.05) use cmarcedit.exe to break then (re)make as utf8
		try:
			for record in reader:
				lccn = record['001'].value().replace(' ','')
				ldr05 = record.leader[5:6]
				if lccn.startswith(schema):
					ward_dict[lccn] = ldr05
		except (UnicodeDecodeError,UnicodeEncodeError) as e:
			logging.info('unicode error - using cmarcedit to convert')
			marc2utf8(m) # break then remake as utf8
			reader = MARCReader(file(m)) # create a new reader
			for record in reader:
				lccn = record['001'].value().replace(' ','')
				ldr05 = record.leader[5:6]
				if lccn.startswith(schema):
					ward_dict[lccn] = ldr05

	# get rid of any lccns that aren't just n or c
	for k,v in ward_dict.items():
		if v in ['d','o','s','x']:
			del ward_dict[k]
	logging.info('removed ldr/05 d,o,s,x ward files')

	for k,v in ward_dict.items():
		ward_lccns.add(str(k))
	logging.info('got list of lccns in ward files')

	return ward_lccns


def get_vger_auth_ids():
	'''
	Use -r to get all lccns from voyager
	'''
	logging.info('getting lccns from voyager')
	
	vger_lccns = set()

	if os.path.isfile(filename): # start afresh with this list
		os.remove(filename)
		msg = 'removed %s' % filename
		print(msg)
		logging.info(msg)

	qstring = """SELECT DISTINCT AUTH_ID,princetondb.GetAuthSubfield(AUTH_MASTER.AUTH_ID,'010','a') as field010a 
FROM AUTH_MASTER"""
	c = db.cursor()
	c.execute(qstring)
	for row in c:
		authid = row[0]
		lccn = row[1]
		if lccn:
			lccn = lccn.replace(' ','')
			row = '%s,%s\n' % (authid,lccn)
			if verbose:
				print str(row)
			with open(filename,'ab+') as vger:
				vger.write(row)
		#else:
		#	pass # auth records with no lccn
	c.close()

	logging.info('got lccns from Voyager')


def marc2utf8(marc):
	'''
	Use MarcEdit cli to 'break' the file from ExLibris then 'make' it as utf-8
	'''	
	try:
		conv = subprocess.Popen(['mono',cmarcedit,'-s',marc,'-d',marc+'.mrk','-break'])
		conv.communicate()
		msg='broke MARC'
		print(msg)
		logging.info(msg)
	except:
		etype,evalue,etraceback = sys.exc_info()
		msg='problem breaking Ward file. %s' % evalue
		print(msg)
		logging.info(msg)
	try:
		conv = subprocess.Popen(['mono',cmarcedit,'-s',marc+'.mrk','-d',marc,'-make','-utf8'])
		conv.communicate()
		msg='made utf-8 file for processing'
		print(msg)
		logging.info(msg)
	except:
		etype,evalue,etraceback = sys.exc_info()
		msg='problem breaking cjk. %s' % evalue
		print(msg)
		logging.info(msg)


def read_dump(schema):
	'''
	read in dump files and compare to ward+vger
	'''
	id_lccns = set()
	dumpfile = 'lc%saf_lccns_from_xml.txt' % schema
	with open('./dump/'+dumpfile) as lcids:
		for i in lcids:
			id_lccns.add(i.strip()) # create a set

	return id_lccns


def make_venn(vw,idloc):
	'''
	Make venn diagram
	'''
	logging.info('making venn diagram')
	venn2([vw, idloc],set_labels = ('vger', 'idloc'))
	plt.show()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate hold reports.')
	parser.add_argument("-v", "--verbose", required=False, default=False, dest="verbose", action="store_true", help="Runtime feedback.")
	parser.add_argument("-n", "--names", required=False, default=False, dest="names", action="store_true", help="Get URIs for names.")
	parser.add_argument("-s", "--subjects", required=False, default=False, dest="subjects", action="store_true", help="Get URIs for subjects.")
	parser.add_argument("-r", "--voyager", required=False, default=False, dest="voyager", action="store_true", help="Get URIs for subjects.")
	args = vars(parser.parse_args())
	subjects = args['subjects']
	names = args['names']
	verbose = args['verbose']
	voyager = args['voyager']

	main()
