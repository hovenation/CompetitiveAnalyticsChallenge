# coding=utf-8

#  above I have set file encoding to utf-8
#  I find this a good practice in scraping data to prevent encoding errors

'''
NOTES

When possible I find it best to write scrapers with http requests as
opposed to browser emulators as that tends to produce more reliable,
and far more resource efficient code, although it does require the extra time 
of mimicking request headers and post data.

I also implemented threading, to show that I am very familiar with both threading
and multiprocessing.  If I needed to run this on large scale, then multiprocessing
would be best to maximize cpu usage.

'''

#  although not always necessary i find it good practice to set 
#  defaults to utf-8 to avoid encoding errors
import sys
reload( sys )
sys.setdefaultencoding( 'utf-8' )

import requests
#from lxml import etree
#  lcml is more efficient that BeautifulSoup but this site was throwing
#  up html parsing errors, so I let BeautifulSoup handle those for me
from bs4 import BeautifulSoup
import re
from threading import Thread, Lock
from collections import OrderedDict

# regular expression to get variables necessary to replicate post request for details
reg_post_vars = re.compile( 'return ApplyNowClick\("(.+?)","(.+?)","(.+?)","(.+?)","(.+?)"\);' )

#  although it does not seem to be neccessary i find it to be good practice
#  to set a real browser user agent to avoid blocking / detection issues
headers = {
	'User-agent' : 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'
	}

class Secure_Cafe():
	
	def __init__( self ):
		self.url = 'https://rubixhollywoodapts.securecafe.com/onlineleasing/rubix-apartments/availableunits.aspx?myOlePropertyId=455235'
		#  use session for easy handling of cookies
		self.session = requests.Session()
		self.lock = Lock()
		
	def get_data( self ):
		http_response = self.session.get( self.url, headers=headers )
		self.soup = BeautifulSoup( http_response.text, 'html.parser' )
		apartments = self.soup.find_all( 'tr', { 'class':'AvailUnitRow' } )
		self.apartment_list = []
		threads = []
		for thread_id in range( len( apartments ) ):
			#  append new item to list in order to maintain results order
			self.apartment_list.append( None )
			thread = Thread( target=self.thread, args=( apartments[thread_id], thread_id ) )
			thread.start()
			threads.append( thread )
		#  wait for all threads to finish
		for thread in threads:thread.join()
		return self.apartment_list
			
	def thread( self, apartment, thread_id ):
		apartment_data = OrderedDict()
		data_points = apartment.find_all( 'td' )
		#  parse out individual data points
		apartment_data['number'] = data_points[0].get_text()
		apartment_data['sq_feet'] = data_points[1].get_text()
		apartment_data['rent'] = data_points[2].get_text()
		apartment_data['deposit'] = data_points[3].get_text()
		post_vars = reg_post_vars.search( str( data_points[4] ) )
		details = self.get_post_result( post_vars.group(1), post_vars.group(2), post_vars.group(3), post_vars.group(4) )
		apartment_data.update( details )
		#  use lock's to ensure that two threads
		#  do not attempt to access the list at the same time
		self.lock.acquire()
		#  assign data to thread id to maintain order
		self.apartment_list[thread_id] = apartment_data
		self.lock.release()
	
	def get_post_result( self, unit_id, floor_plan_id, property_id, move_in_date ):
		#  get the data from the details page and the terms pop up
		#  and merge them together in a dict for appending to the preliminary data
		details_html = self.make_details_post_request( unit_id, floor_plan_id, property_id, move_in_date )
		details_data_points = self.parse_details_page( details_html )
		terms_html = self.make_terms_get_request( details_data_points['lease_info']['Move-in Date'], unit_id, floor_plan_id, property_id )
		terms_data = self.parse_terms_data_page( terms_html )
		details_data_points['terms_data'] = terms_data
		return details_data_points
	
	def make_details_post_request( self, unit_id, floor_plan_id, property_id, move_in_date ):
		#  we have to imitate the post request normally handled by javascript
		url = 'https://rubixhollywoodapts.securecafe.com/onlineleasing/rubix-apartments/termsandotheritems.aspx'
		#  set headers to mimick the request made by the browser
		headers = {
			'User-agent' : 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
			'Referer' : self.url,
			'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'Accept-Language' : 'en-US,en;q=0.5',
			'Accept-Encoding' : 'gzip, deflate, br',
			'Content-Type' : 'application/x-www-form-urlencoded'
			}
		post_vars = {
			'isViaForm' : 1,
			'UnitID' : unit_id,
			'FloorPlanID' : floor_plan_id,
			'myOlePropertyId' : property_id,
			'MoveInDate' : move_in_date,
			'src' : ''
			}
		http_response = self.session.post( url, headers=headers, data=post_vars )
		return http_response.text
		
	def parse_details_page( self, html ):
		soup = BeautifulSoup( html, 'html.parser' )
		
		apartment_summary_data = OrderedDict()
		apartemnt_summary_rows = soup.find( 'div', attrs={'id':'AptSummary'} ).find_all( 'tr' )
		#  use a loop and copy the key value pairs used by site to speed things up
		for row in apartemnt_summary_rows:
			row_data = row.find_all( 'td' )
			key = row_data[0].get_text().strip()
			#  because of the way the address is listed i need to set the key manually
			if key == '':key = 'Address2'
			apartment_summary_data[ key ] = row_data[1].get_text()
			
		lease_info_data = OrderedDict()
		lease_info_rows = soup.find( 'div', attrs={'id':'LeaseInfoSummary'} ).find_all( 'tr' )
		#  use a loop and copy the key value pairs used by site to speed things up
		for row in lease_info_rows:
			row_data = row.find_all( 'td' )
			lease_info_data[ row_data[0].get_text().strip() ] = row_data[1].get_text().strip()
		
		details_data_points = OrderedDict()
		
		pricing_info_div = soup.find( 'div', attrs={'id':'divPricingInfo'} )
		pricing_info_div_rows = pricing_info_div.find_all( 'div', attrs={'class':'row-fluid'} )
		for row in pricing_info_div_rows:
			row_data = row.find_all( 'div' )
			details_data_points[ row_data[0].get_text().strip() ] = row_data[1].get_text().strip()
		#  get rid of the see price options field since it is not what we want
		#  I use a try catch to bypass the error from a not common error
		#  when certain data is not available for a listing
		try:del details_data_points['See price options']
		except KeyError:pass
		return {
			'details_data' : details_data_points,
			'lease_info' : lease_info_data,
			'apartment_summary' : apartment_summary_data
			}
		
	def parse_terms_data_page( self, html ):
		soup = BeautifulSoup( html, 'html.parser' )
		table_rows = soup.find_all( 'tr' )
		terms_data = OrderedDict()
		for row in table_rows:
			row_data = row.find_all( 'td' )
			#  I use a try catch to skip an unwanted row
			try:terms_data[ row_data[0].get_text().strip() ] = row_data[1].get_text().strip()
			except IndexError:pass
		return terms_data
		
	def make_terms_get_request( self, date, unit_id, floor_plan_id, property_id ):
		url = 'https://rubixhollywoodapts.securecafe.com/rcloadcontent.ashx?contentclass=pricingmatrixlro&&DtNextMatrixStart=' + date + '&ShowLess=0&IsReadOnly=No&UnitId=' + unit_id + '&MinLeaseTerm=3&MaxLeaseTerm=12&Floorplanid=' + floor_plan_id + '&myOlePropertyid=' + property_id + '&MoveInDate=' + date + '&UnitAvailableDate=' + date + '&ISRCOLE=False&isOpen=-1&cafeportalkey='
		http_response = self.session.get( url, headers=headers )
		return http_response.text



