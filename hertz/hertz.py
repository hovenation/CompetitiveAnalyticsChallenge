# coding=utf-8

'''
NOTES
	for this challenge I found the specifc http request responsible for
retrieving the required data.  Instead of scraping the data off the page, I think the easier more eloquent
solution is to simply query these services and get the json data directly.
	This code here could easily be transported to a Selenium / PahtomJS or a 
PhantomJS only solution to mimimize cpu usage, but for time consideration I 
used Selenium and Firefox.
	It looks like this page is working by posting the zip code and product id's
to https://www.hertzequip.com/herc/handlers/RentalsEquipmentDetailsHandler
which then, I assume stores the zip code you entered as a server side session
variable, since the requests for specific data do not require the input of zip 
code or product id's but seem to know what to deliver after that post request
is made.
	This tells me it may be possible to make this scraper without the use of a
browser / browser emulator, however that would require getting the proper product
id's to replicate the post request and I could not easily find those as they seem
to be generated by javascript, so I went ahead and used a browser to handle all 
of that for me
'''

import sys
reload( sys )
sys.setdefaultencoding( 'utf-8' )

from selenium.webdriver import Firefox
import json
from collections import OrderedDict
from time import sleep

class Hertz():
	def __init__( self ):
		self.driver = Firefox()
		#self.driver.get( 'https://www.hertzequip.com/herc/rental-equipment/aerial-equipment+manlifts+articulating-boom-lift' )
		self.driver.implicitly_wait( 15 )
		
	def perform_search( self, zip_code ):
		self.driver.get( 'https://www.hertzequip.com/herc/rental-equipment/aerial-equipment+manlifts+articulating-boom-lift' )
		#  wait for javascript to load the page before we begin
		self.driver.find_element_by_xpath( '//span[text()="View Rates"]' )
		#  selenium commands can be very unreliable
		#  since Jquery is already loaded, I'll use that
		self.driver.execute_script( """
			$('span:contains("View Rates")')[0].click()
			$('input[id="postalCode"]').val('""" + zip_code + """')
			$('a[class="button_four button_four_skin"]')[0].click()
			""" )
		#  wait a few seconds for page element to disappear
		sleep( 3 )
		#  wait until javascript has loaded the page again
		self.driver.find_element_by_xpath( '//span[text()="View Rates"]' )
			
	def get_rates( self ):
		rates_info_json = self.driver.execute_script( """	
			var xmlhttp = new XMLHttpRequest()
			var url = "https://www.hertzequip.com/herc/rest/rentals/getBuilderEquipmentDetailsItemInfo?catalogType=" + String( catalogType ) + "&categoryId=" + categoryId + "&subcategory1Id=" + subcategory1Id + "&subcategory2Id=" + subcategory2Id + "&_=" + String( new Date().getTime() )
			xmlhttp.open( "GET", url, false )
			xmlhttp.send()
			return xmlhttp.responseText
			""" )
		return rates_info_json
			
	def get_store_info( self ):
		store_info_json = self.driver.execute_script( """
			var xmlhttp = new XMLHttpRequest()
			var url = "https://www.hertzequip.com/herc/rest/rentals/getBuilderJobLocationsItemInfo?_=" + String( new Date().getTime() )
			xmlhttp.open( "GET", url, false )
			xmlhttp.send()
			return xmlhttp.responseText
			""" )
		return store_info_json
		
	def perform_search_get_data( self, zip_code ):
		self.perform_search( zip_code )
		location_data = json.loads( self.get_store_info() )
		equipment_rates_data = json.loads( self.get_rates() )
		specific_data = OrderedDict()
		specific_data['branch_zip_code'] = location_data['data']['jobLocation']['branchLocation']['zip']
		specific_data['branch_id'] = location_data['data']['jobLocation']['branchLocation']['branch']
		specific_data['equipment_list'] = []
		for equipment in equipment_rates_data['data']['equipmentInfo']['m_list']:
			equipment_data = OrderedDict()
			equipment_data['specs'] = [ equipment['spec1'], equipment['spec2'] ]
			equipment_data['makes & models'] = equipment['makesModels']['m_list']
			equipment_data['rates'] = equipment['ratesInfo']
			specific_data['equipment_list'].append( equipment_data )
		return { 
			'location_data' : location_data,
			'equipment_rates_data' : equipment_rates_data,
			'specific_data' : specific_data
			}
		
		
		