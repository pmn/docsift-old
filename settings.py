# Global settings
import os

APP_SECRET_KEY = '~QfzJFPEN+%/}8.;Bk91KwR=3=ni D!IY+d<+kX0x*k`;oRE5+Ag)Cj`{,D93s-%'
AWS_ACCESS_ID = os.getenv("AWS_ACCESS_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
DATABASE_URI = 'sqlite:////tmp/test.db'
TURK_HOST = 'mechanicalturk.amazonaws.com'
TURK_TEST_HOST = 'mechanicalturk.sandbox.amazonaws.com'
