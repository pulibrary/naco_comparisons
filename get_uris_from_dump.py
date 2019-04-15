#!/usr/bin/env python
#-*- coding: utf-8 -*-
import argparse
import logging
import os
import requests
import urlparse
from lxml import etree
'''
Get lccns from id.loc dump. Best run on the ec2 instance where the data lives.
Get xml response and parse it.
from 201902
pmg
'''

def main(host,outfile):
	get_ids(host,outfile)
	parse(outfile)


def get_ids(host,outfile):
	'''
	Get ids from fuseki. Returns xml.
	'''
	query = '''SELECT ?s WHERE {
  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.loc.gov/mads/rdf/v1#Authority> .
  FILTER NOT EXISTS { ?s <http://www.loc.gov/mads/rdf/v1#useInstead> ?o } .
  FILTER NOT EXISTS { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.loc.gov/mads/rdf/v1#Variant> } .
  FILTER NOT EXISTS { ?s <http://www.loc.gov/mads/rdf/v1#useInstead> ?u } .
  FILTER NOT EXISTS { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> 
  <http://www.loc.gov/mads/rdf/v1#DeprecatedAuthority> } .
}'''
	data = { 'query': query}
	headers={ 'Content-Type':'application/x-www-form-urlencoded','Accept':'application/sparql-results+xml' }
	r = requests.post(host + "sparql", data=data, headers=headers)
	#if verbose:
	#	print r.text
	with open(outfile+'.xml','a+') as outfiletxt: #names is too big for this method
		print r.text
		outfiletxt.writelines(r.text)


def parse(outfile):
	'''
	Parse fuseki xml
	'''
	nsmap = {}
	with open(outfile+'.xml','rb') as xmL, open(outfile+'_from_xml.txt','wb+') as report:
		import xml.etree.ElementTree as etree
		for event, elem in etree.iterparse(xmL,events=('end', 'start-ns')):
			if event == 'end':
				lccn = elem.text
				if lccn and lccn.startswith('http'):
					lccn = os.path.basename(lccn)
					if verbose:
						print(lccn)
					report.writelines(lccn+'\n')
				elem.clear()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Get uris from id.loc dump.')
	parser.add_argument("-v", "--verbose", required=False, default=False, dest="verbose", action="store_true", help="Runtime feedback.")
	parser.add_argument("-n", "--names", required=False, default=False, dest="names", action="store_true", help="Get URIs for names.")
	parser.add_argument("-s", "--subjects", required=False, default=False, dest="subjects", action="store_true", help="Get URIs for subjects.")
	args = vars(parser.parse_args())
	names = args['names']
	subjects = args['subjects']
	verbose = args['verbose']

	if names:
        	host = "http://localhost:3030/lcnaf/"
        	outfile = "lcnaf_lccns"
	elif subjects:
        	host = "http://localhost:3030/lcsaf/"
        	outfile = "lcsaf_lccns"


	main(host,outfile)
