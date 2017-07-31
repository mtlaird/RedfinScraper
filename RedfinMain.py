import RedfinScraperPages as RfSP
import csv
import RedfinSql as RfSql
from time import sleep
from os import listdir


def get_redfin_favorites_csv(csv_path='.'):

    files = listdir(csv_path)
    csv_files = []
    for f in files:
        split_filename = f.split('_')
        if split_filename[0] == 'redfin' and split_filename[-1] == 'results.csv':
            csv_files.append(f)

    csv_files.sort(reverse=True)
    return csv_files[0]


if __name__ == '__main__':

    session = RfSql.Session()
    csv_file = get_redfin_favorites_csv()
    with open(csv_file)as f:
        reader = csv.DictReader(f)
        for row in reader:
            house_url = row['URL (SEE http://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)']
            print 'Getting house details from {} ...'.format(house_url)
            try:
                scraped_house = RfSP.RedfinHomePage(house_url, init=True)
            except AttributeError:
                print 'Could not parse information from {} '.format(house_url)
                continue
            print 'Adding house at {} to database ...'.format(scraped_house.address)
            redfin_sql_house = RfSql.RedfinHouse(scraped_house.get_detailed_json())
            redfin_sql_house.add_to_db(session)
            print 'Waiting for five seconds ...'
            sleep(5)
