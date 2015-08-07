from django.shortcuts import render
from django.http import HttpResponse
from django.http import QueryDict
import json
import scraper

# Create your views here.
def home(request):
	raceId = request.GET.get('raceId','2278373444')
	raceName = request.GET.get('raceName','taiwan')
	bib = request.GET.get('bib',443)
	startTime = request.GET.get('startTime','07:00:00')

	# testVal = { 'a': '123', 'b': '456'}
	# valStr = json.dumps(testVal)
	scraperResults = scraper.getRaceData(raceId, raceName, bib, startTime)
	response = HttpResponse(scraperResults)
	response['content-type'] = 'application/json'
	response['Access-Control-Allow-Origin'] = '*'
	return response