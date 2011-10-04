### docsift: a system for categorizing text

## Stuff you should change: 
Open up settings.py and modify all the keys you need to change. 

It's especially important to modify the DATABASE_URI as it's currently set to create a database in /tmp (You don't want to lose all your data on reboot!)

In mturk.py, you'll want to change the value for "host" at line 16 - by default it's set to connect to the Mechanical Turk sandbox to make sure everything else is good before incurring costs.

## Once you have configured everything: 
Start the tool with

    python main.py

Browse to http://localhost:5000


