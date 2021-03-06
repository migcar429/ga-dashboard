import argparse

from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools

from xlwings import Workbook, Range, Sheet
import os.path

def main():
	# Defines the scope of authorization to request from Google. Relies on permissions set to account on Google Analytics. 
	scope = ['https://www.googleapis.com/auth/analytics.readonly']

	# Both created via Google Developer Console. 
	# Key file must be in the same directory as this script; Account email must be given permission at ACCOUNT level on Google Analytics account.
	service_acccount_email_location = '/Users/Mig/desktop/google_service_account_email.txt'
	key_file_location = '/Users/Mig/desktop/client_secrets.p12'

	# Read key from file.
	f = open(service_acccount_email_location, 'r')
	service_account_email = f.read()
	f.close()

	# API details.
	api_name = 'analytics'
	api_version = 'v3'

	# Obtain a service object.
	service = get_service(api_name, api_version, scope, key_file_location, service_account_email)
	
	# Obtain the organic search traffic data from the relevant profiles.
	profile_id = get_profile_id(service)
	results = get_organic_results(service, profile_id)

	# Obtain the organic search traffic data from custom-set goals.
	goal_id = get_goal_id(service, profile_id)
	goal_results = get_goal_results(service, profile_id, goal_id)	
	
	# Write all results to Excel file.
	write_to_excel(results, goal_results)

def get_service(api_name, api_version, scope, key_file_location, service_account_email):

	# Open the key file. Output is str.
	f = open(key_file_location, 'rb')
	key = f.read()
	f.close()

	# Create oAuth credentials, authorize an http object with said credentials.
	credentials = SignedJwtAssertionCredentials(service_account_email, key, scope=scope)
	http = credentials.authorize(httplib2.Http())

	# Build the service using authorized http object and API details.
	service = build(api_name, api_version, http=http)

	return service


def get_profile_id(service):
	# Gets the right values for accountId, webPropertyId, profileId, checks if they exist and declares global variables for re-use.
	# List all accounts that the service_account_email has access to.
	accounts = service.management().accounts().list().execute()

	if accounts.get('items'):
		# Obtain the ID of the relevant account.
		global account
		account = accounts.get('items')[0].get('id')
		
		print accounts.get('items')[0].get('name')

		properties = service.management().webproperties().list(accountId=account).execute()

		if properties.get('items'):
			# Obtain the ID of the relevant webProperty.
			global property 
			property = properties.get('items')[0].get('id')
			
			print properties.get('items')[0].get('name')

			profiles = service.management().profiles().list(accountId=account, webPropertyId=property).execute()

			if profiles.get('items'):
				# Obtain the ID of the relevant profile (view).
				global profile
				profile = profiles.get('items')[1].get('id')

				print profiles.get('items')[1].get('name')
				return profile
				
				# Print all the profiles (views) and their IDs.
				'''n = 0
				for dictionary in profile:
					print profile[n]['name'] + ' ' + str(profile[n]['id'])
					n += 1'''

	return None


def get_organic_results(service, profile_id):
	# Returns organic search data for every month and appends to a list. ids, start_date, end_date and metrics are REQUIRED. 
	# https://developers.google.com/analytics/devguides/reporting/core/v3/reference for list of parameters.
	
	# Create a list with number of days in each month (to use as end_date parameter). Also checks in leap year.
	global year
	year = 2015

	global daysinmonth
	if year % 4 == 0:
		daysinmonth = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	else:
		daysinmonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

	# Create a list with number of days in each month w/ for loops and appending.
	'''
	daysinmonth = []

	for n in range(1, 13):
		if n in [1, 3, 5, 7, 8, 10, 12]:
			lastday = 31
			daysinmonth.append(lastday)
		elif n == 2:
			if year % 4 == 0:
				lastday = 29
				daysinmonth.append(lastday)
			else:
				lastday = 28
				daysinmonth.append(lastday)
		else:
			lastday = 30
			daysinmonth.append(lastday)'''

	# Loop through and request sessions from organic search for each month in the year. Then append to empty list.
	global intermed
	intermed = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
	trafficdata = []

	for i in range(0, 12):
		ga_request = service.data().ga().get(ids='ga:' + profile_id,
			start_date='%s-%s-01' % (year, intermed[i]),
			end_date='%s-%s-%s' % (year, intermed[i], daysinmonth[i]),
			metrics='ga:sessions',
			dimensions='ga:medium',
			filters='ga:medium==organic',
			fields='rows',
			prettyPrint='true').execute()

		if not ga_request:
			trafficdata.append(0)
		else:
			# First list index required ([0]) because of strange formatting. Second list index is from a list with format ['organic', value].
			trafficdata.append(int(ga_request['rows'][0][1]))

	print trafficdata
	return trafficdata
	
def get_goal_id(service, profile_id):
	# List all goals you have access to with the relevant account gained from get_profile_id().
	goals = service.management().goals().list(profileId=profile, accountId=account, webPropertyId=property).execute()

	if goals.get('items'):
		goal = goals.get('items')[0]['id']
		return goal


def get_goal_results(service, profile_id, goal_id):
	# Gets goal traffic data.
	goaltrafficdata = []
	
	if goal_id in range(0, 9):
		zero = '0'
	elif goal_id > 9:
		zero = ''

	for i in range(0, 12):
		ga_request = service.data().ga().get(
			ids='ga:' + profile_id,
			start_date='%s-%s-01' % (year, intermed[i]),
			end_date='%s-%s-%s' % (year, intermed[i], daysinmonth[i]),
			metrics='ga:goal' + zero + goal_id + 'Completions',
			filters='ga:medium==organic',
			).execute()

		if not ga_request:
			goaltrafficdata.append(0)
		else:
			goaltrafficdata.append(ga_request['totalResults'])

	print goaltrafficdata
	return goaltrafficdata


def write_to_excel(results, goal_results):
	# Writes data to excel.

	# Specifies path of Excel file and sets the current workbook to it.
	path = os.path.dirname(os.path.abspath(__file__))
	filename = 'test.xlsx'
	wb = Workbook(path + '/' + filename)

	# Transpose the list of results to be able to fit xlwings format of inputting values column-wise.
	results = map(list, zip(results))
	goal_results = map(list, zip(goal_results))

	# Sets values to cells.
	Range('Sheet1', 'A1').value = results
	Range('Sheet1', 'B1').value = goal_results


if __name__ == '__main__':
	main()