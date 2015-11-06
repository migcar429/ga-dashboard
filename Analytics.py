import argparse

from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools


def main():
	# Defines the scope of authorization to request from Google. Relies on permissions set to account on Google Analytics. 
	scope = ['https://www.googleapis.com/auth/analytics.readonly']



	# Both created via Google Developer Console. 
	# Key file must be in the same directory as this script; Account email must be given permission at ACCOUNT level on Google Analytics account.
	service_acccount_email_location = '/Users/Mig/desktop/google_service_account_email.txt'
	key_file_location = '/Users/Mig/desktop/client_secrets.p12'

	f = open(service_acccount_email_location, 'r')
	service_account_email = f.read()
	f.close()

	# API details.
	api_name = 'analytics'
	api_version = 'v3'

	service = get_service(api_name, api_version, scope, key_file_location, service_account_email)
	results = get_organic_results(service, get_profile_id(service))
	# print_column_headers(results)
	


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
	# List all accounts that the service_account_email has access to.
	accounts = service.management().accounts().list().execute()

	if accounts.get('items'):
		# Obtain the ID of the relevant account.
		account = accounts.get('items')[0].get('id')
		
		print accounts.get('items')[0].get('name')

		properties = service.management().webproperties().list(accountId=account).execute()

		if properties.get('items'):
			# Obtain the ID of the relevant webProperty.
			property = properties.get('items')[0].get('id')
			
			print properties.get('items')[0].get('name')

			profiles = service.management().profiles().list(accountId=account, webPropertyId=property).execute()

			if profiles.get('items'):
				# Obtain the ID of the relevant profile (view).
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
	# Returns data from specified parameters. ids, start_date, end_date and metrics are REQUIRED. 
	# https://developers.google.com/analytics/devguides/reporting/core/v3/reference for list of parameters.
	
	# Create a list with number of days in each month (to use as end_date parameter).
	year = 2015

	if year % 4 == 0:
		data = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	else:
		data = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

	# Create a list with number of days in each month w/ for loops and appending.
	'''
	data = []

	for n in range(1, 13):
		if n in [1, 3, 5, 7, 8, 10, 12]:
			lastday = 31
			data.append(lastday)
		elif n == 2:
			if year % 4 == 0:
				lastday = 29
				data.append(lastday)
			else:
				lastday = 28
				data.append(lastday)
		else:
			lastday = 30
			data.append(lastday)'''

	# Loop through and request sessions from organic search for each month in the year.
	intermed = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
	trafficdata = []

	for i in range(0, 12):
		
		ga_request = service.data().ga().get(ids='ga:' + profile_id,
			start_date='2015-%s-01' % intermed[i],
			end_date='2015-%s-%s' % (intermed[i], data[i]),
			metrics='ga:sessions',
			dimensions='ga:medium',
			filters='ga:medium==organic',
			fields='rows').execute()

		trafficdata.append(ga_request)

	print trafficdata


	'''return service.data().ga().get(
		ids='ga:' + profile_id,
		start_date=start_date,
		end_date=end_date,
		metrics='ga:sessions',
		dimensions='ga:medium',
		filters='ga:medium==organic',
		fields='rows').execute()'''

'''def print_column_headers(results):
	headers = results['columnHeaders']

	for header in headers:
		print header.get('name')'''
	

if __name__ == '__main__':
	main()