import json 
import datetime 
import dateutil.parser
import tweepy
from bs4 import BeautifulSoup
import urllib2
import time
import random

#
# Tweets # of days of school left and school closing/delay info @hacountdown
#

startDate = [] 
endDate = [] 

halfDays = [] 
offDays = [] 

snowDaysFull = [] 
snowDaysTwoHrDly = [] 

oAuthConsumerKey = 'XXXXXXXXXXXXXXXXXXXXXXXXX'
oAuthConsumerSecret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
oAuthAccessToken = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
oAuthAccessTokenSecret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

tweetedStatusToday = False 

DEBUG = True
SIMULATE = True 
simulationDays = 25
simulationTime = simulationDays * 48

def main(): 
	corrected = False 
	cycleNo = 0 

	global tweetedStatusToday
	global SIMULATE

	loadData()
	
	auth = tweepy.OAuthHandler(oAuthConsumerKey, oAuthConsumerSecret)
	auth.set_access_token(oAuthAccessToken, oAuthAccessTokenSecret)

	api = tweepy.API(auth)

	while True:
		# get current time
		if SIMULATE: 
			now = datetime.datetime.now() + datetime.timedelta(minutes=30*cycleNo)
		else:
			now = datetime.datetime.now()

		# if is half day and is around noon, tweet days left
		if isHalfDay(datetime.datetime.date(now)) and now.hour == 12 and now.minute <= 30: 
			tweetDaysLeft(api, now)
			print str(now)
			print '------------'
		# if is full day and near end of day tweet days left
		elif isSchoolDay(datetime.datetime.date(now)) and now.hour == 14 and now.minute <= 30 and not isHalfDay(datetime.datetime.date(now)): 
			tweetDaysLeft(api, now) 
			print str(now)
			print '------------'
		# if day ended and tweeted reset var
		if now.hour >= 21 and tweetedStatusToday:
			tweetedStatusToday = False 

		# if didnt tweet today, tweet
		if not tweetedStatusToday:
			tweetSchoolClosingStatus(api)

		# if not a debug simulation sleep program
		if not SIMULATE:
			if corrected: 
				time.sleep(60 * 30)  # sleep 30 mins
			else: 
				time.sleep(60 * (60 - now.minute))  # sleep up to next hour mins
				corrected = True 
		else: 
			cycleNo += 1 
			
		if cycleNo == simulationTime: 
			print 'Completed ' + str(simulationDays) + ' days'
			break 
		
# ---------------------------------------- # 	
#   Helper functions to be used by main    #
# ---------------------------------------- #

# loads JSON data into global variables
def loadData():
	try:
		dateData = json.loads(open('data.json', 'r').read())
		parse = dateutil.parser.parse
		startDate.append(datetime.datetime.date(parse(dateData['startDate'])))
		endDate.append(datetime.datetime.date(parse(dateData['endDate'])))
		
		loadDates(dateData, 'halfDays', halfDays)
		loadDates(dateData, 'offDays', offDays)
		
		loadDates(dateData, 'newSnowDaysFull', snowDaysFull)
		loadDates(dateData, 'newSnowDaysTwoHrDly', snowDaysTwoHrDly)
		
	except IOError as e: 
		print "ERROR: Couldn't find data file"
		exit() 
	except: 
		print 'ERROR: Exiting due to unknown error'
		exit()


# loads array of json dates from data with key 'named' to 'toVar'
def loadDates(data, named, toVar): 	
	for date in data[named]: 
		toVar.append(datetime.datetime.date(dateutil.parser.parse(date))) 


def printState(): 
	if not DEBUG:
		return 
	print str(startDate)
	print str(endDate)
	
	print str(halfDays)
	print str(offDays)
	
	print str(snowDaysFull)
	print str(snowDaysTwoHrDly)


def isSchoolDay(now): 
	return isWeekDay(now) and isInSchoolYear(now) and not isOffDay(now) and not isSnowDay(now)


def isWeekDay(now): 
	return now.isoweekday() in range(1,6) 


def isInSchoolYear(now): 
	return now >= startDate[0] and now <= endDate[0]


def isOffDay(now): 
	return now in offDays 


def isSnowDay(now): 
	return now in snowDaysFull


def isHalfDay(now): 
	return now in halfDays

# calculates the number of school days left based on loaded JSON data
def calculateDaysLeft(today): 
	physicalDaysLeft = int(str(endDate[0] - datetime.datetime.date(today)).split()[0])
	schoolDaysLeft = 0 
	for i in range(physicalDaysLeft):
		now = datetime.datetime.date(today + datetime.timedelta(days=i))
		if isHalfDay(now):
			schoolDaysLeft += 0.5 
		elif isSchoolDay(now) or isSnowDay(now): 
			schoolDaysLeft += 1 
	return schoolDaysLeft

# Fetches, parses, and returns school closing status string
def getSchoolClosingStatus():
	global SIMULATE
	if SIMULATE:
		return ''
	#https://web.archive.org/web/20170210032754/http://local.wnep.com/transfers/school.html
	urlStr = 'http://local.wnep.com/transfers/school.html'
	html = BeautifulSoup(urllib2.urlopen(urlStr).read(), 'html.parser')
	statusStr = '' 
	for row in html.body.find_all('td'): 
		if 'Hanover Area' in str(row): 
			statusStr = str(row.find('font', {'class', 'status'}).text)
	return statusStr 


# Constructs and sends days left tweet
def tweetDaysLeft(api, now): 
	msg = randomMessageForFile('dailyMessages.txt').replace('XXX', str(calculateDaysLeft(now)))
	if DEBUG: 
		print 'UPDATE STATUS: ' + msg
	else: 
		api.update_status(msg)


# Constructs and sends school closed tweet
def tweetSchoolClosingStatus(api): 
	global SIMULATE
	status = getSchoolClosingStatus()
	if status == '': return 
	
	if status == "2 HR DELAY": 
		msg =  randomMessageForFile('delayMessages.txt') 
	elif status == "CLOSED":
		msg = randomMessageForFile('closingMessages.txt')
	else: 
		if len(status) <= 140:
			msg = status
		else: 
			overflowCount = len(status) - 140 - 3
			msg = status[:overflowCount] + '...' 
	if SIMULATE:
		print 'UPDATE STATUS: ' + msg
	else: 
		api.update_status(msg)
	tweetedStatusToday = True 

# returns a random line from file
def randomMessageForFile(fileName): 
	options = open(fileName, 'r').read().split('\n')[:-1]
	rand = random.randint(0, len(options) - 1)
	return options[rand]

if __name__ == "__main__":
	main() 
