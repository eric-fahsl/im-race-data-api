from bs4 import BeautifulSoup
import urllib
# import xmlHelper
import json
import random
from datetime import datetime

##RUN SECTION
# sectionIndex = xmlHelper.searchContentForTag("RUN DETAILS", "", "", "", str(soup), 0)[1]

# distanceResult = xmlHelper.searchContentForTag("km", "", "<td>", "</td>", str(soup), sectionIndex)
# distanceTime = xmlHelper.searchContentForTag("km", "", "<td>","</td", str(soup), distanceResult[1])
# sectionIndex = distanceTime[1]
# print [distanceResult[0], distanceTime[0], sectionIndex]

# xmlHelper.searchContentForTag("km", "km", "<td>", "</td>", str(soup), 19534)

# distanceUnit = "km"

def createSoup(url) :
	#snowUrl = "http://www.snow-forecast.com/resorts/White-Pass/feed.xml"
	snowPage = urllib.urlopen(url)
	soup = BeautifulSoup(snowPage)
	return soup

def convertStringTimeToSeconds(stringTime) :
	#First check if it is empty, ie --:--
	if stringTime[0] == "-" :
		return 0
	times = stringTime.split(':')
	seconds = 0
	if len(times) > 2 :
		seconds = 3600*int(times[0]) + 60*int(times[1]) + int(times[2])
	else :
		seconds = 60*int(times[0]) + int(times[1])
	return int(seconds)

def convertSecondsToTime(seconds) :
	seconds = int(round(seconds, 0))
	hours = seconds / 3600
	minutes = format((seconds / 60) % 60, '02d')
	sec = format(seconds % 60, '02d')
	convertedTime = minutes + ":" + sec
	if hours > 0 :
		convertedTime = str(hours) + ":" + convertedTime
	return convertedTime

def calculatePacePerHr(distance, seconds) :
	if seconds == 0 :
		return 0
	hours = seconds / 3600.0
	pace = distance/hours
	return round(pace, 2)

def convertPerHourToMinPer(mph) :
	secPerPace = 3600.0 / mph
	return convertSecondsToTime(secPerPace)

def calculateEstimatedTime(distance, pace) :
	if pace == 0 :
		return convertSecondsToTime(0)
	estimatedHours = float(distance) / pace
	estimatedSeconds = estimatedHours * 3600
	return convertSecondsToTime(estimatedSeconds)

def createSportObject(soup, sportTableIndex, startTimeSeconds) :

	sportObject = {}
	# sportObject["activity"] = sportName
	sportObject["splits"] = []
	runSoup = soup.find_all('table')[sportTableIndex]
	runSplits = list(runSoup.find_all('tr'))
	
	#for calculating average
	aggregatedTimeSeconds = 0
	aggregatedDistance = 0
	averageSoFar = 0
	latestRaceTimeStr = "--:--"
	latestEstimatedRaceTimeStr = "--:--"
	index = 0
	for i in range(2) :
		del runSplits[0]
	for tr in runSplits :
		tds = tr.find_all('td')
		split = {}
		split["totalDistance"] = tds[0].string.encode('ascii', 'ignore').replace('km', '').replace('mi', '')
		split["splitDistance"] = tds[1].string.replace('km', '').replace('mi','')
		split["splitTime"] = tds[2].string
		split["pace"] = tds[3].string
		split["raceTime"] = tds[4].string

		splitSeconds = convertStringTimeToSeconds(split["splitTime"])
		split["estimatedRaceTime"] = "--:--"
		split["estimatedTimeOfDay"] = "--:--"
		#Handle Total Row Differently
		totalDistance = split["totalDistance"]
		if split["totalDistance"] == "Total" :
			totalDistance = split["splitDistance"]
			splitSeconds = 0
		
		if splitSeconds > 0 :
			aggregatedDistance += float(split["splitDistance"])
			aggregatedTimeSeconds += splitSeconds
			averageSoFar = calculatePacePerHr(aggregatedDistance, aggregatedTimeSeconds)

		if aggregatedDistance > 0 :		
			split['activityElapsedTime'] = convertSecondsToTime(aggregatedTimeSeconds)
			split["estimatedTime"] = calculateEstimatedTime(totalDistance, averageSoFar)
			splitEstimatedSeconds = calculateEstimatedTime(split["splitDistance"], averageSoFar)
			split["splitEstimatedTime"] = splitEstimatedSeconds
			latestRaceTimeSec = convertStringTimeToSeconds(split["raceTime"])
			if index > 0 :
				latestRaceTimeSec = convertStringTimeToSeconds(latestRaceTimeStr)
				if latestRaceTimeSec == 0 :
					latestRaceTimeSec = convertStringTimeToSeconds(latestEstimatedRaceTimeStr)
				estimatedRaceTimeSec = latestRaceTimeSec + convertStringTimeToSeconds(splitEstimatedSeconds)
				split["estimatedRaceTime"] = convertSecondsToTime( estimatedRaceTimeSec )
				split["estimatedTimeOfDay"] = convertSecondsToTime(startTimeSeconds + estimatedRaceTimeSec)

			
			#if its the last one, 
			if split["totalDistance"] == "Total" :
				split["estimatedRaceTime"] = latestEstimatedRaceTimeStr
				split["estimatedTimeOfDay"] = latestEstimatedTimeOfDayStr
				


			# split["estimatedRaceTime"] = convertSecondsToTime(convertStringTimeToSeconds(latestRaceTime) \
			# 	+ convertStringTimeToSeconds(splitEstimatedSeconds))
		
		# print splitSeconds, totalDistance, aggregatedTimeSeconds, averageSoFar
		

		# print totalDistance, averageSoFar	
		# split["estimatedTime"] = calculateEstimatedTime(totalDistance, averageSoFar)
		latestRaceTimeStr = split["raceTime"]
		latestEstimatedRaceTimeStr = split["estimatedRaceTime"]
		latestEstimatedTimeOfDayStr = split["estimatedTimeOfDay"]
		sportObject['splits'].append(split)
		index += 1

	if aggregatedDistance > 0 :
		sportObject['averagePerHour'] = calculatePacePerHr(aggregatedDistance, aggregatedTimeSeconds)
		sportObject['perMinuteAverage'] = convertPerHourToMinPer(sportObject['averagePerHour'])

	return sportObject

def getTransitionData(soup, transitionIndex) :
	transitionSplits = list(soup.find_all('table')[transitionIndex].find_all('tr'))
	transitionData = {}
	transitionData['T1'] = transitionSplits[0].find_all('td')[1].string
	transitionData['T2'] = transitionSplits[1].find_all('td')[1].string
	return transitionData


def getLatestUpdate(allSports) :
	sports = ["swim","run"]
	lastSplit = {}
	for sport in sports :
		latestUpdate = getLastNextSplit(allSports[sport])
		if latestUpdate != {} and latestUpdate != None:
			latestUpdate["sport"] = sport
			return latestUpdate
	return {}

def getLastNextSplit(raceData) :
	#print raceData

	lastNextSplit = {}
	for split in raceData["splits"] :
		lastNextSplit['next'] = split	
		if split["raceTime"] == '--:--' :
			return lastNextSplit
		lastNextSplit['previous'] = split
	return {}

def getRaceData(raceId='2278373444', race='taiwan', bib=443, raceStartTime='07:00:00') :
	timeStart = datetime.now()

	# RACE_ID = "2278373444"
	# RACE_ID="2278373444"
	# RACE = "taiwan"
	# BIB = 443
	# BIB=1571
	randomNum = int(random.uniform(0,100))
	# url = "http://tracking.ironmanlive.com/mobilesearch.php?rid=2278373444&race=taiwan&y=2015&athlete=559#axzz3X0O9WgL1"
	url = "http://tracking.ironmanlive.com/mobilesearch.php?rid=" + raceId + "&race=" + race + "&y=2015&athlete=" + str(bib) + "#axzz3X0O9W" + str(randomNum)
	# url = "http://tracking.ironmanlive.com/mobileathlete.php?rid=2147483676&race=florida70.3&bib=1571&v=3.0&beta=&1428859800#axzz3X6WZscVO"
	#print url

	soup = createSoup(url)
	
	raceStartTimeSeconds = convertStringTimeToSeconds(raceStartTime)

	allSports = {}
	allSports["name"] = soup.h1.string
	allSports["state"] = soup.find(text="State").findNext('td').string
	allSports["url"] = url
	allSports["bib"] = bib

	allSports["swim"] = createSportObject(soup, 2, raceStartTimeSeconds)
	allSports["bike"] = createSportObject(soup, 3, raceStartTimeSeconds)
	allSports["run"] = createSportObject(soup, 4, raceStartTimeSeconds)

	allSports["transition"] = getTransitionData(soup, 5)
	allSports["lastNextSplit"] = getLatestUpdate(allSports)

	timeEnd = datetime.now()
	allSports["elapsedTime"] = (timeEnd - timeStart).total_seconds()

	return json.dumps(allSports)