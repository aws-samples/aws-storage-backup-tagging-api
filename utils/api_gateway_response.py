# API Gateway expects json objects.
# Some web server implementations, such as the flash, uses single quote in
# its response. Use this function to convert a dict into double quoted string.
import json


class DoubleQuoteDict(dict):
    def __str__(self):
        return json.dumps(self)
