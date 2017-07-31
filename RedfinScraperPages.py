from bs4 import BeautifulSoup
import requests


def make_redfin_url(home_id, state='IN', city='Indiapanolis'):

    return 'https://www.redfin.com/{}/{}/home/{}'.format(state, city, home_id)


class RedfinHomePage:
    def __init__(self, url, init=False):
        self.url = url
        self.request = None
        self.dom = None
        self.address = None
        self.price = None
        self.beds = None
        self.baths = None
        self.sqft = None
        self.redfinprice = None
        self.desc = None
        self.key_details = {}
        self.home_facts = {}
        self.property_details = {}
        self.property_history = {}
        if init:
            self.get_dom()
            self.parse_dom()

    def get_basic_json(self):
        return {'url': self.url, 'address': self.address, 'price': self.price, 'beds': self.beds, 'baths': self.baths,
                'sqft': self.sqft, 'redfinprice': self.redfinprice, 'desc': self.desc}

    def get_detailed_json(self):
        basic = self.get_basic_json()
        basic['key_details'] = self.key_details
        basic['home_facts'] = self.home_facts
        basic['property_details'] = self.property_details
        basic['property_history'] = self.property_history
        return basic

    def get_dom(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/47.0.2526.80 Safari/537.36'}
        self.request = requests.get(self.url, headers=headers)
        self.dom = BeautifulSoup(self.request.text, 'html.parser')

    def parse_dom(self):
        self.address = self.dom.find('span', class_='street-address').text + self.dom.find('span',
                                                                                           class_='citystatezip').text
        try:
            self.price = self.dom.find('span', {'itemprop': 'price'}).text
        except AttributeError:
            self.price = self.dom.find('div', {'data-rf-test-id': 'abp-price'}).findChild(class_='statsValue').text
        self.beds = self.dom.find('div', {'data-rf-test-id': 'abp-beds'}).findChild(class_='statsValue').text
        self.baths = self.dom.find('div', {'data-rf-test-id': 'abp-baths'}).findChild(class_='statsValue').text
        self.sqft = self.dom.find('div', {'data-rf-test-id': 'abp-sqFt'}).findChild(class_='statsValue').text
        try:
            self.redfinprice = self.dom.find('span', {'data-rf-test-id': 'avmLdpPrice'}).findChild(class_='value').text
        except AttributeError:
            try:
                self.redfinprice = self.dom.find('div', {'data-rf-test-id': 'avm-price'}).find('div').text
            except AttributeError:
                pass
        try:
            self.desc = self.dom.find('div', class_='remarks').text
        except AttributeError:
            pass
        for kd in self.dom.find_all('div', class_='keyDetail'):
            self.key_details[kd.findChild(class_='header').text] = kd.findChild(class_='content').text
        for tr in self.dom.find('div', class_='facts-table').find_all('div', class_='table-row'):
            if tr.find('div', class_='table-value').text != u'\u2014':
                self.home_facts[tr.find('span', class_='table-label').text] = tr.find('div', class_='table-value').text

        if self.dom.find('div', class_='amenities-container'):
            for pdt in self.dom.find('div', class_='amenities-container'):
                pdtname = pdt.find('div', class_='super-group-title').text
                pdtcontent = {}
                for ag in pdt.find_all(class_='amenity-group'):
                    agname = ag.find('h4', class_='title').text
                    agcontent = {}
                    for agli in ag.find_all('li'):
                        if ':' in agli.text:
                            agcontent[agli.text.split(':')[0]] = agli.text.split(':')[1].strip()
                        else:
                            agcontent[agli.text] = True
                    pdtcontent[agname] = agcontent
                self.property_details[pdtname] = pdtcontent

        history_rows = self.dom.find('div', id='property-history-transition-node').find_all('tr')

        if len(history_rows) > 1:
            for i in range(1, len(history_rows)):
                history_json = {}
                history_row_cells = history_rows[i].find_all('td')
                date = history_row_cells[0].text
                history_json['event'] = history_row_cells[1].find('div').text
                if '$' in history_row_cells[2].text:
                    history_json['price'] = history_row_cells[2].text
                self.property_history[date] = history_json


class RedfinSearchPage:
    def __init__(self, url, init=False):
        self.url = url
        self.request = None
        self.dom = None
        self.links = []
        if init:
            self.get_dom()
            self.parse_dom()

    def get_dom(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/47.0.2526.80 Safari/537.36'}
        self.request = requests.get(self.url, headers=headers)
        self.dom = BeautifulSoup(self.request.text, 'html.parser')

    def parse_dom(self):
        for tr in self.dom.find_all('tr', class_='tableRow'):
            self.links.append('http://www.redfin.com' + tr.find('div', class_='address').find('a')['href'])
