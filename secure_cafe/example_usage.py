
import json
import secure_cafe

instance = secure_cafe.Secure_Cafe()
apartment_data = instance.get_data()
result_number = len( apartment_data )
print( str( result_number ) + ' results collected' )

open( 'apartment_data.json', 'w' ).write( json.dumps( apartment_data, indent=4 ) )

