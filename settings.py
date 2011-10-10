# Global settings
import os

PORT = 5000

APP_SECRET_KEY = '~QfzJFPEN+%/}8.;Bk91KwR=3=ni D!IY+d<+kX0x*k`;oRE5+Ag)Cj`{,D93s-%'
AWS_ACCESS_ID = os.getenv("AWS_ACCESS_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
DATABASE_URI = 'sqlite:////Users/paulnakata/dev/docsift/testing/docsift.db'
THRESHOLD = 65 # This should get moved to the campaign at some point
TURK_PROD_HOST = 'mechanicalturk.amazonaws.com'
TURK_TEST_HOST = 'mechanicalturk.sandbox.amazonaws.com'

# Change this to whichever turk host you want to use
TURK_HOST = TURK_TEST_HOST
