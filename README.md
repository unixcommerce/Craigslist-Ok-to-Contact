# Craigslist-Ok-to-Contact

Introducing the Craigslist Ok to Contact Scraper. This python scraper makes it easy to find contacts on Craigslist to reach out to and offer your services.

Simply include the category of the section on craigslist into the input.csv file and run the scraper with the following command. 

cd Scraper
python3 Craigslist_Scraper_1.1.0.py -s=10

-s flag represents a time delay between each section being crawled by scraper

In this example, the scraper will pause for 60 seconds between each page

python3 /home/opc/Scraper/Craigslist_Scraper_1.1.1.py -s=60

System reqirments 

python 3.9
pandas
requests
parsel
tqdm

I hope you find this useful. It is very powerful if used in conjunction with a CRM
~ 

###### Duplicate send issue corrected. This was due to an issue updating database permissions
###### Also, early termination will trigger graceful exit while updating database.

*** The Scraper has been updated to work with proxy and API based pages. Please contact for details

admin@unixcommerce.com
