#!/bin/python
# -*- coding: utf-8 -*-

# houzz scraper

import re
import csv
import sys
import argparse
from bs4 import BeautifulSoup
import urllib.request 
from argparse import ArgumentParser
import time
from fake_useragent import UserAgent
import random
from urllib.request import Request, urlopen

ua = UserAgent() # From here we generate a random user agent
proxies = [] # Will contain proxies [ip, port]

parser = argparse.ArgumentParser(description='test', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-z', '--zipcode', help='specify ZIP Code.', required=True)
parser.add_argument('-o', '--output', help='specify output filename. default is houzz.csv', nargs='?', default='houzz.csv', type=str)
parser.add_argument('-m', '--miles', help='specify range in miles (10,20,50,100), default is 50.', nargs='?', default=50, type=int)
parser.add_argument('-d', '--depth', help='specify page depth (0-300 recommended). defualt is 5.', nargs='?', default=5, type=int)
parser.add_argument('-s', '--sort', help='specify sort type ((m)ost reviews, (b)est match, (r)ecent reviews). default is recent reviews.', nargs='?', default='r', type=str)
parser.add_argument('-p', '--profession', help='''specify profession. default is architect.
		((a)rchitect, (d)esign-build, (g)eneral-contractor,
		(h)ome-builders, (i)interior-designer, (k)itchen-and-bath, 
		(k)itchen-and-bath-(r)emodeling [kr], (l)andscape-architect, 
		(l)andscape-(c)ontractor [lc], (s)tone-pavers, (t)ile-stone-and-countertop, 
		(all) CAUTION - using 'all' could cause tens of thousands of page requests to be made)''', nargs='?', default='a', type=str)
args = parser.parse_args()


hzbaseurl = 'http://www.houzz.com/professionals'
knownlinks = []

# the goods will end up here
businesslist = []

# translate argument into corresponding URL chunk
def pro(p):
	return {

                # new added categories 
                'c': 'cabinets',
                'ca': 'carpenter',
                'dec': 'decks-and-patios',
                'p': 'driveways-and-paving',
                'f': 'fencing-and-gates',
                'fire': 'fireplace',
                'gd': 'garage-doors',
                'han': 'handyman',
                'iron': 'ironwork',
                'pwc': 'paint-and-wall-coverings',
                'sid': 'siding-and-exterior',
                'sc': 'specialty-contractors',
                'sta': 'staircases',
                'spc': 'stone-pavers-and-concrete',
                'wc': 'window-coverings',
                'w': 'windows',
                'hvac': 'hvac-contractors',
                'tile': 'electrical-contractors',
                'esar': 'environmental-services-and-restoration',
                'fur': 'furniture-refinishing-and-upholstery',
                'gals': 'garden-and-landscape-supplies',
                'las': 'lawn-and-sprinklers',
                'mov': 'movers',
                'pain': 'painters',
                'pc': 'pest-control',
                'gdr': 'garage-door-repair',
                'pc': 'plumbing-contractors',
                'rg': 'roofing-and-gutter',
                'sptas': 'septic-tanks-and-systems',
                'sapm': 'spa-and-pool-maintenance',
                'ts': 'tree-service',
                'cc': 'carpet-cleaners',
                'chim': 'chimney-cleaners',
                'exc': 'exterior-cleaners',
                'hc': 'house-cleaners',
                'rr': 'rubbish-removal',
                'wcc': 'window-cleaners',
                'door': 'doors',
                
		
                # original categories | "all" will do all categories that are in the dictonary

                'd': 'design-build',
		'g': 'general-contractor',
		'h': 'home-builders',
		'i': 'interior-designer',
		'k': 'kitchen-and-bath',
		'kr': 'kitchen-and-bath-remodeling',
		'l': 'landscape-architect',
		'lc': 'landscape-contractor',
		's': 'stone-pavers-and-concrete',
		't': 'tile-stone-and-countertop',
		'all': [ 'design-build', 'general-contractor', 'home-builders', 'interior-designer', 'kitchen-and-bath', \
				'kitchen-and-bath-remodeling', 'landscape-architect', 'landscape-contractor', 'stone-pavers-and-concrete', \
				'tile-stone-and-countertop''cabinets','carpenter','decks-and-patios','driveways-and-paving','fencing-and-gates',\
                        'fireplace','garage-doors','handyman','ironwork','paint-and-wall-coverings','siding-and-exterior','specialty-contractors',\
                        'staircases','stone-pavers-and-concrete','window-coverings','windows','hvac-contractors','electrical-contractors',\
                        'environmental-services-and-restoration','furniture-refinishing-and-upholstery','garden-and-landscape-supplies',\
                        'lawn-and-sprinklers','movers','painters','pest-control','garage-door-repair','plumbing-contractors','roofing-and-gutter',\
                        'septic-tanks-and-systems','spa-and-pool-maintenance','tree-service','carpet-cleaners','chimney-cleaners','exterior-cleaners',\
                        'house-cleaners','rubbish-removal','window-cleaners','doors'] ,
        'temp': ['general-contractor','home-builders','kitchen-and-bath-remodeling','garage-doors','hvac-contractors','painters','electrical-contractors','plumbing-contractors','roofing-and-gutter','driveways-and-paving','landscape-contractor','tile-stone-and-countertop','decks-and-patios','cabinets', 'garage-door-repair']

	}.get(p, 'all')
	
# do the same here
def sorttype(s):
	return {
		'm': 'sortReviews',
		'b': 'sortMatch',
		'r': 'sortRecentReviews'
	}.get(s, 'sortMatch')


# nom nom nom
def yumSoup(page, profession):
	zipcode = args.zipcode
	miles = args.miles
	sortby = sorttype(args.sort)
	# create the search URL
	hzsearchurl = '{0}/{1}/c/{2}/d/{3}/{4}/p/{5}'.format(hzbaseurl, profession, zipcode, miles, sortby, page)
	
	opener = urllib.request.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0 (Linux i686)')]
	response = opener.open(hzsearchurl)
	content = response.read()
	soup = BeautifulSoup(content,"lxml")

	return soup
	

# create a list of business details within a list of businesses for later use
# start each business list with it's houzz URL
def getLinks(page, profession):
	soup = yumSoup(page, profession)
	dirtylinks = str(soup.find('script', {'type' : 'application/ld+json'}))
	cleanlinks = re.findall('http[^"]*', dirtylinks)
	for link in cleanlinks:
		if link.startswith('http://www.houzz.com/professionals/') or link.startswith('http://schema.org') or link in knownlinks:
			continue
		knownlinks.append(link)
		newbusinessurl = [link]
		businesslist.append(newbusinessurl)
		numberofbusinessurl = len(businesslist)

		print(numberofbusinessurl)
		


# fill out info for each business. sends one page request per firm
def buildCards(businesslist):
	for business in businesslist:
		response = urllib.request.urlopen(business[0])
		content = response.read()
		soup = BeautifulSoup(content,"lxml")
		# most of the contact info is here
		
		
		try:
			
			phonenumber = str(soup.find('span', {'class' : 'pro-contact-text'}).a.get('phone'))

		except AttributeError:
			phonenumber = 'Phone:N/A'
		# there is an edge case where some firms have a website and no phone number, which mangles the phone number section
		# if this is the case, we go find the website elsewhere in the page contents
		if phonenumber == 'Website':
			phonenumber = soup.find('div', {'class' : 'pro-contact-methods one-line'}).a.get('href')
		
		# populate nested business lists

		business.append(phonenumber)

		

		# show off what we're packaging
	
	
		print (phonenumber)
		print ("")
		print ("")
		
def writeCSV(outputfile):
	# get it into csv
	with open(outputfile, 'a') as ofile:
		writer = csv.writer(ofile)
		writer.writerow(('URL','Phone'))
		for business in businesslist:
			writer.writerow((business[0], business[1]))


def stageOneScraper(profession):
	# the URL page counter increments by 15.
	pagedepth = int(args.depth) * 15
	for page in range(0, pagedepth, 15):
		getLinks(page, profession)


def stageTwoScraper():
	buildCards(businesslist)
	


def main(): 
# Retrieve latest proxies
	proxies_req = Request('https://www.sslproxies.org/')
	proxies_req.add_header('User-Agent', ua.random)
	proxies_doc = urlopen(proxies_req).read().decode('utf8')

	soup = BeautifulSoup(proxies_doc, 'html.parser')
	proxies_table = soup.find(id='proxylisttable')

	# Save proxies in the array
	for row in proxies_table.tbody.find_all('tr'):
		proxies.append({
			'ip':row.find_all('td')[0].string,
			'port':row.find_all('td')[1].string
			})

	# Choose a random proxy
	proxy_index = random_proxy()
	proxy = proxies[proxy_index]

	for n in range(1, 100):
		req = Request('http://icanhazip.com')
		req.set_proxy(proxy['ip'] + ':' + proxy['port'], 'http')

	# Every 10 requests, generate a new proxy
	if n % 10 == 0:
	  proxy_index = random_proxy()
	  proxy = proxies[proxy_index]
	  print("New Proxy Generated")
	# Make the call
	try:
	  my_ip = urlopen(req).read().decode('utf8')
	  print('Using IP #' + str(n) + ': ' + my_ip)
	except: # If error, delete this proxy and find another one
	  del proxies[proxy_index]
	  print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' deleted.')
	  proxy_index = random_proxy()
	  proxy = proxies[proxy_index]

	profession = pro(args.profession)
	if type(profession) is list:
		print('caution: you have chosen "all". if you have a large page depth set, you might want to get a coffee..')
		for p in profession:
			stageOneScraper(p)
	else:
		stageOneScraper(profession)
	stageTwoScraper()
	outputfile = args.output
	writeCSV(outputfile)
	print("-Scraper Has Finished-")

# Retrieve a random index proxy (we need the index to delete it if not working)
def random_proxy():
  return random.randint(0, len(proxies) - 1)
  print("Proxy not working, retreving a new one")




	
	
if __name__ == '__main__':

	main()
