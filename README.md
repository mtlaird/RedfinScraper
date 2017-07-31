# RedfinScraper

This script creates an Sqlite database with details about houses that you've favorited from the 
real estate website www.redfin.com. There are also SqlAlchemy classes allowing you to use the
information from that database in python applications.

## Setup

This script requires the following modules:

1) Requests
2) BeautifulSoup
3) SqlAlchemy

All can be found and installed using pip.

To get the houses you have favorited on Redfin, go https://www.redfin.com/myredfin/favorites
and click the 'Download' link. Then place the resulting csv file in the RedfinScraper directory.

## Usage

To run the script, run

    python RedfinMain.py
    
And watch the output. When the script finishes, you should have `db.sqlite` file in the 
directory, which contains the information about the houses from your favorites list which
could be parsed using the parsing library.

## Caveats

Note that since this script relies on screen-scraping, any minor changes Redfin makes to
the structure of their pages could cause it to fail.  
