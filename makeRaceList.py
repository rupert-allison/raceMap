## Create a csv file containing race data scraped from fellrunner.org.uk
## Usual usage woudl e.g. create YorkDales2017.csv, all races in the Dales in 2017.

## Requirements: (np, matplotlib,) requests, Beautiful Soup.
## Module 'requests' was already installed on my machine/python version.
## Need to have Beautiful Soup python module installed to parse webpage html
## see here: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
## for documentation. I installed with: sudo pip-3.4 install beautifulsoup4

import numpy as np
import matplotlib.pyplot as plt
import sys
from bs4 import BeautifulSoup as bs
import requests
import re

from OSGB import *
from OSTN02 import *
import transform

###############################################################################
## User parameters: 
## May need to adjust 'lastRaceID' for processes a new year of race fixtures 
## Also change 'outDir' to location appropriate for your machine. 
###############################################################################

## Area and year of interest. Naming should follow fellrunner.org.uk convention, 
## with no spaces or punctuation. Last four characters should specify year. 
tag = '2017' ## Currently only 2017 supported

## Set directory to output .csv file
outDir = '/Users/allisonradmin/Documents/Programs/raceMap/data/'

################################################################################


def scrapePage( raceID ):
	## Given page id, return race info as a dictionary
	
	## Instantiate a dictionary to hold race information
	race = {'web': 'http://fellrunner.org.uk/races.php?id=' + raceID}

	## Use requests to grab the html from webpage, then beautifulSoup to parse
	page = requests.get( race['web'] )
	page = bs( page.content, 'html.parser' )

	## Find race details, and check date relevant for year tag
	try:
		details  = page.find(id="main-content-left").find_all(class_="race_info_list")[0].find_all('li')
		race['date']   = details[0].get_text()[12:].strip()
	except: 
		race['date'] = ''

	if tag in race['date']:
		## Find race name
		racename = page.find(class_="title_races").get_text()[19:].strip()
		if racename[-3:] == '(R)': racename = racename[:-4]
		race['name'] = racename.replace(',',' ')

		## And just read in the rest of the data!
		for item in details:
			text = item.get_text()
			if 'Distance' in text:
				race['dist']  = text[9:].strip()
				if race['dist'] != 'Unknown':
					race['miles'] = float(re.sub('.*/ ','',race['dist']).strip()[:-1])
				else:
					race['miles'] = 0.
			if 'Climb' in text:
				race['ascent'] = text[6:].strip()
				if race['ascent'] != 'Unknown':
					race['climb'] = int( re.sub('/.*','',race['ascent']).strip()[:-1] )
				else:
					race['climb'] = 0
				if race['climb'] < 0: race['climb'] = 0
			if 'Venue' in text:
				race['venue'] = text[6:].replace(', ', ' ').replace(',',' ').replace('. ',' ').replace('.',' ').replace(' nr ',' ').replace(' Nr ',' ').replace(' near ',' ').replace('GR','').strip()
				gr = race['venue'].split(' ')
				gr = [ x for x in gr if (len(x) == 8 and x[2:].isdigit()) ]
				if len(gr) == 1: 
					gr = gr[0]	
					if gr[2:].isdigit() and (not gr.isdigit()) and (len(gr) in [8,12]): 
						if len(gr) ==  8: xin, yin = parse_grid(gr[:2], int(gr[2:5]+'00'), int(gr[5:]+'00'))
						if len(gr) == 12: xin, yin = parse_grid(gr[:2], int(gr[2:7])     , int(gr[7:])     )
						try:
							(x,y,h) = OSGB36_to_ETRS89 (xin, yin)
							(gla, glo) = grid_to_ll(x, y)
							race['latlong'] = '%.6f %.6f' % (gla, glo)
							print(race['latlong'])
							print('GR FROM VENUE: SUCCESS')
						except:
							pass
				
			if 'Country:' in text:
				race['country'] = text[8:].strip()
				if race['country'] == 'Northern Ireland': 
					race['region'] = race['country']
			if 'Region' in text:
				race['region'] = text[7:].strip()
			if 'Grid ref' in text:
				gr = text[9:].replace('GR','').replace(' ','').strip()
				if gr[2:].isdigit() and (not gr.isdigit()) and (len(gr) in [8,12]): 
					if len(gr) ==  8: xin, yin = parse_grid(gr[:2], int(gr[2:5]+'00'), int(gr[5:]+'00'))
					if len(gr) == 12: xin, yin = parse_grid(gr[:2], int(gr[2:7])     , int(gr[7:])     )
					try:
						(x,y,h) = OSGB36_to_ETRS89 (xin, yin)
						(gla, glo) = grid_to_ll(x, y)
						race['latlong'] = '%.6f %.6f' % (gla, glo)
						print(race['latlong'])
					except:
						pass
		if 'region' in race:
			if race['country'] != 'England':
				race['region'] = race['country'] 
			if race['country'] == 'England - Not FRA':
				race['region'] = 'Unknown'
		#if 'region' in race:
		#	if race['country'] != 'England':
		#		race['region'] = race['region'] + '(' + race['country'] + ')'

		if ('region' not in race) or (race['region'] == 'Unknown'):# or (race['dist'] == 'Unknown'):
			print('Region unknown, not adding ' + race['name'] + ' to race list')
			race = {}
			
	else:	## If not correct year, just return an empty dictionary, which is parsed correctly (i.e. then ignored) by listRace
		race = {}	
	return race	

def listRace( race ):
	## race should be dictionary containing race info
	## This function works out automatically which file to write to based on region.
	if bool(race):
		if 'latlong' in race:
			race['gmap'] = race['latlong']
		else:
			race['gmap'] = race['venue']
		print('Processing race: ' + race['name'])
		with open( outDir + tag + '.csv', 'a' ) as f:
			f.write("%s,%s,%s,%s,%s,%s,%s,%.1f,%d,%s,%s \n" % (race['date'], race['name'], race['dist'], race['ascent'], race['venue'], race['country'], race['region'], 
										race['miles'], race['climb'], race['gmap'], race['web']) )

def setDataFile():
	## overwrite any existing file, insert appropriate header.
	with open( outDir + tag + '.csv', 'w' ) as f:
		f.write('Date, Race, Distance, Ascent, Venue, Country, Region, Distance (mil), Climb (m), Gmap, Web\n')
		f.close()
def main():
	## Make relevant file and add header
	setDataFile()

	## Do the dirty work: trawl the webpages for races in year
	## defined by user parameter 'tag'. Save these to .csv file readable by google maps.
	
	if tag == '2017':
		firstInd = 4480
		lastInd  = 5336
	else:
		print('Use index numbers in makeRaceList.py to efficiently trawl fellrunner.org.uk races, given the year of interest\nExiting...')
		sys.exit()
	for i in np.arange( firstInd, lastInd + 1 ):
		race = scrapePage( str(i) )
		listRace( race )


main()
