## Create a csv file containing race data scraped from fellrunner.org.uk
## REDUNDANT: Usual usage woudl e.g. create YorkDales2017.csv, all races in the Dales in 2017.
## Version 1 of the race map had 871 views when released publically in July 2018. 

## Requirements: (np, matplotlib,) requests, Beautiful Soup.
## Module 'requests' was already installed on my machine/python version.
## Need to have Beautiful Soup python module installed to parse webpage html
## see here: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
## for documentation. I installed with: sudo pip-3.4 install beautifulsoup4

## To do (12th July 2018):
## - Add Scottish Hill Races from scottishhillracing.co.uk
## - Add random perturbation to those races at repeat locations for ease of viewing (e.g. Trunce)
## - **DONE** Prefix each race name with the Date (e.g. 04/06 Trunce 3) such that they come up in date order. 
## - **DONE** Auto make a JanFeb file and a NovDec file (only 10 layers max allowed).
## - **DONE** Fix 18/02 Stybarrow Dodd race - Thirlmere address


## Manual modifications:
## Fellside: --> "Fellside Village, Caldbeck"
## Slieve Donard --> "Newcastle Main Street Northern Ireland"


import numpy as np
import matplotlib.pyplot as plt
import sys
from bs4 import BeautifulSoup as bs
import requests
import re
import subprocess

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
tag = '2018' ## Currently only 2017/2018 supported

## Set directory to output .csv file
outDir = '/Users/allisonradmin/Documents/Programs/raceMap/data/'

################################################################################

def formatDate( date ):
	## Takes in a string with long format date and outputs day and month as string in format DD/MM
	date  = date.split()
	month = date[2]
	day   = date[1]

	if month == 'Jan': month = '01'
	if month == 'Feb': month = '02'
	if month == 'Mar': month = '03'
	if month == 'Apr': month = '04'
	if month == 'May': month = '05'
	if month == 'Jun': month = '06'
	if month == 'Jul': month = '07'
	if month == 'Aug': month = '08'
	if month == 'Sep': month = '09'
	if month == 'Oct': month = '10'
	if month == 'Nov': month = '11'
	if month == 'Dec': month = '12'

	if len(day) == 3: day = '0' + day[:1]
	if len(day) == 4: day =       day[:2]

	return day+'/'+month+' '

def scrapeSHRpage():
	## Grab all of this year's races from the SHR website; returns a list of races, each 
	## element containing a dictionary detailing a given race. 

	races = []
	
	page = requests.get( 'http://scottishhillracing.co.uk/Races.aspx' )
	page = bs( page.content, 'html.parser' )

	details = page.find(id="tabcontainer_body").find_all("a", {"id" : lambda l: l and l.startswith('dgRacesAll_a1_')})#.find_all('li')
	print(len(details))
	print(type(details))
	details = page.find(id="tabcontainer_body").find_all("td", {"style" : "width:350px;"})#.find_all('li')
	print(len(details))
	print(type(details))
scrapeSHRpage()
sys.exit()

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
		#print(race['date'].split())
		race['month']  = race['date'].split()[2]
		race['shortdate'] = formatDate( race['date'] )	
		print(race['shortdate'])
	except: 
		race['date'] = ''
		race['month'] = '' 

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


				## Manual interventions:

				if race['name'] == 'Slieve Donard': race['venue'] += ' Northern Ireland'
				if race['name'] == 'Fellside': race['venue'] += ' Caldbeck'
				if race['name'] == 'Stybarrow Dodd Kong Winter Series 4': race['venue'] += ' CA12 4TJ'
				
				## End of manual intervention

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
		with open( outDir + tag + race['month'] +'.csv', 'a' ) as f:
			f.write("%s,%s,%s,%s,%s,%s,%s,%.1f,%d,%s,%s \n" % (race['date'], race['shortdate'] + race['name'], race['dist'], race['ascent'], race['venue'], race['country'], race['region'], 
										race['miles'], race['climb'], race['gmap'], race['web']) )

def setDataFile(month = ''):
	## overwrite any existing file, insert appropriate header.
	with open( outDir + tag + month + '.csv', 'w' ) as f:
		if (month != 'Feb' and month != 'Dec'): 
			f.write('Date, Race, Distance, Ascent, Venue, Country, Region, Distance (mil), Climb (m), Gmap, Web\n')
		f.close()
def main():
	## Make relevant file and add header
	#setDataFile()
	for mon in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
		setDataFile(month = mon)

	## Do the dirty work: trawl the webpages for races in year
	## defined by user parameter 'tag'. Save these to .csv file readable by google maps.
	
	if tag == '2017':
		firstInd = 4480
		lastInd  = 5336
		#firstInd = 4890
		#lastInd  = 4900
	if tag == '2018':
		firstInd = 5337
		lastInd  = 5996 
		#lastInd  = 5390 
	else:
		print('Use index numbers in makeRaceList.py to efficiently trawl fellrunner.org.uk races, given the year of interest\nExiting...')
		sys.exit()
	for i in np.arange( firstInd, lastInd + 1 ):
		race = scrapePage( str(i) )
		listRace( race )

	## Now sort the various files into date order
	for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
		subprocess.call(['sort', '-k2', '-n', '-o', outDir + tag + month + '.csv', outDir + tag + month + '.csv' ])

	## Concatenate Jan/Feb and Nov/Dec since google only allows 10 layers per map. 
	with open(outDir + tag + 'JanFeb.csv', 'w') as outfile:
    		subprocess.call(['cat', outDir + tag + 'Jan.csv', outDir + tag + 'Feb.csv'], stdout=outfile)
	with open(outDir + tag + 'NovDec.csv', 'w') as outfile:
    		subprocess.call(['cat', outDir + tag + 'Nov.csv', outDir + tag + 'Dec.csv'], stdout=outfile)

main()



"""
## REDUNDANT - SEE ABOVE.
## Note, use:
cp 2018Oct.csv 2018OctNovDec.csv
cat 2018Nov.csv 2018OctNovDec.csv
cat 2018Dec.csv 2018OctNovDec.csv
## to put the data files into one, since Google Maps limits to 10 layers.
"""

