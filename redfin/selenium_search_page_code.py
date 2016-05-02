
'''
this is a selenium version of grabbing data from the search page
not necessary since all this data is available on the property page.
'''

	def loop_through_results_table( self ):
		self.properties_list = []
		page_number = 1
		while True:
			for row in self.driver.find_elements_by_xpath( '//tbody[@class="tableList"]/tr' ):
				cells = row.find_elements_by_tag_name( 'td' )
				property_data = OrderedDict()
				property_data['address'] = cells[1].text.strip()
				property_data['location'] = cells[2].text.strip()
				property_data['price'] = cells[3].text.strip()
				property_data['beds'] = cells[4].text.strip()
				property_data['baths'] = cells[5].text.strip()
				property_data['sq_feet'] = cells[6].text.strip()
				row.text
				row.click()
				#  wait for data to load, use try catch to avoid an error halting execution
				try:self.driver.find_element_by_xpath( '//span[@class="street-address"][contains( text(),"' + property_data['address'] + '" )]' )
				except:pass
				for span in self.driver.find_elements_by_xpath( '//span[@class="citystatezip"]/span' ):
					property_data[ span.get_attribute( 'class' ).strip() ] = span.text.strip()
				details_data = self.driver.find_element_by_class_name( 'amenities' )
				for list_item in details_data.find_elements_by_tag_name( 'li' ):
					spans = list_item.find_elements_by_tag_name( 'span' )
					property_data[ spans[0].text.strip() ] = spans[1].text.strip()
				property_data[ 'url' ] = self.driver.find_element_by_xpath( '//a[@data-rf-test-id="address-link-xDP"]' ).get_attribute( 'href' )
				self.properties_list.append( property_data )
			try:
				self.driver.find_element_by_xpath( '//a[@data-rf-test-id="react-data-paginate-page-' + str( page_number ) + '"]' )
				self.driver.find_element_by_xpath( '//a[@data-rf-test-id="react-data-paginate-page-' + str( page_number ) + '"]' ).click()
				page_number += 1
			except:break
			
	def scrape_property_page( self, page_url ):
		self.driver.get( page_url )
		