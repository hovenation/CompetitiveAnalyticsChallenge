

from hertz import Hertz
import json
from collections import OrderedDict

general_data = OrderedDict()
specific_data = OrderedDict()
hertz = Hertz()
for zip in [ '92626', '10001', '32011', '73301', '60290' ]:
	results_data = hertz.perform_search_get_data( zip )
	general_data[zip] = results_data
	specific_data[zip] = results_data['specific_data']
		
open( 'general_data.json', 'w' ).write( json.dumps( general_data, indent=4 ) )
open( 'specific_data.json', 'w' ).write( json.dumps( specific_data, indent=4 ) )
hertz.driver.quit()