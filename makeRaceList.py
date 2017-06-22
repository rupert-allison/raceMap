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

###############################################################################
## User parameters: 
## May need to adjust 'lastRaceID' for processes a new year of race fixtures 
## Also change 'outDir' to location appropriate for your machine. 
###############################################################################

## Area and year of interest. Naming should follow fellrunner.org.uk convention, 
## with no spaces or punctuation. Last four characters should specify year. 
tag = '2017'

## Set directory to output .csv file
outDir = '/Users/allisonradmin/Documents/Programs/raceMap/data/'

## At fellrunnner.org.uk, race ID's start from 1000 and, in 2017, end at 5336
firstRaceID = '1000'
lastRaceID  = '5336'

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
		race['name'] = racename.replace(',','')

		## And just read in the rest of the data!
		for item in details:
			text = item.get_text()
			if 'Distance' in text:
				race['dist']  = text[9:].strip()
				if race['dist'] != 'Unknown':
					race['miles'] = float( re.sub('.*/','',race['dist']).strip()[:-1] )
				else:
					race['miles'] = 0.
			if 'Climb' in text:
				race['ascent'] = text[6:].strip()
				if race['ascent'] != 'Unknown':
					race['climb'] = int( re.sub('/.*','',race['ascent']).strip()[:-1] )
				else:
					race['climb'] = 0
				print(race['climb'])
			if 'Venue' in text:
				race['venue'] = text[6:].replace(',', '').replace('.','').replace(' nr ','').replace(' Nr ','').replace(' near ','').strip()
			if 'Region' in text:
				race['region'] = text[7:].strip()
	
		if ('region' not in race) or (race['region'] == 'Unknown') or (race['dist'] == 'Unknown'):
			race = {}
		#race['dist']   = details[5].get_text()[9:].strip()
		#race['ascent'] = details[6].get_text()[6:].strip()
		#race['venue']  = details[7].get_text()[6:].strip()
		
	else:	## If not correct year, just return an empty dictionary, which is parsed correctly (i.e. then ignored) by appendRace
		race = {}	
	return race	

def appendRace( race, regions, regionTags ):
	## race should be dictionary containing race info
	## This function works out automatically which file to write to based on region.
	if bool(race):
		for i, region in enumerate( regions ):
			if race['region'] == region:
				print('Processing race: ' + race['name'])
				with open( outDir + regionTags[i] + tag + '.csv', 'a' ) as f:
					f.write("%s,%s,%s,%s,%s,%s \n" % (race['date'], race['name'], race['dist'], race['ascent'], race['venue'], race['web']) )

def setDataFiles( regionTags ):
	## overwrite any existing files, insert appropriate headers.
	for regionTag in regionTags:
		with open( outDir + regionTag + tag + '.csv', 'w' ) as f:
			f.write('Date, Race, Distance, Ascent, Venue, Web\n')
			f.close()


def getRegions():
	## Scrape the region names from the website and process for tags.
	## Returns list of regions and corresponding tags.
	page = requests.get( 'http://fellrunner.org.uk/races.php' )
	page = bs( page.content, 'html.parser' )
	reg = page.find(id='left-col').find_all(class_='fp_r_list')[4].find_all('li')[2:15]
	reg = [region.get_text() for region in reg]
	regTag = [region.replace('/','').replace('.','').replace(' ','') for region in reg] ## Remove spurious punctuation and space for clarity in file name
	return reg, regTag

## Scrape region names of interest and define corresponding file tag. 
## Make relevant files and add header
regions, regionTags = getRegions()
setDataFiles( regionTags )

## Do the dirty work: trawl the webpages for races in year
## defined by user parameter 'tag'. Save these to .csv file readable by google maps.
for i in np.arange( 4700, 5340 ):
	race = scrapePage( str(i) )
	appendRace( race, regions, regionTags )
