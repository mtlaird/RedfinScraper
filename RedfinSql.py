from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
import time

Base = declarative_base()
engine = create_engine('sqlite:///db.sqlite')
Session = sessionmaker(bind=engine)


class PropertyHistoryEvent(Base):
    __tablename__ = "property_history"

    house_id = Column(Integer, ForeignKey('houses.id'), primary_key=True)
    date = Column(Integer, primary_key=True)
    readable_date = Column(String)
    event = Column(String)
    price = Column(String)

    def __init__(self, json_data=None):

        if json_data:
            self.load_from_simple_json(json_data)

    def load_from_simple_json(self, j):

        for key in j:
            self.__dict__[key] = j[key]


class HouseDetail(Base):
    __tablename__ = "house_details"

    house_id = Column(Integer, ForeignKey('houses.id'), primary_key=True)
    category = Column(String, primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String)

    def __init__(self, json_data=None):

        if json_data:
            self.load_from_simple_json(json_data)

    def load_from_simple_json(self, j):

        for key in j:
            self.__dict__[key] = j[key]


class RedfinHouse(Base):
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True)
    url = Column(String)
    address = Column(String)
    price = Column(String)
    beds = Column(String)
    baths = Column(String)
    sqft = Column(String)
    desc = Column(String)
    redfinprice = Column(String)

    details = relationship('HouseDetail')
    history = relationship('PropertyHistoryEvent', order_by='desc(PropertyHistoryEvent.date)')

    def __init__(self, json_data=None):

        self.json_data = json_data
        if json_data:
            self.load_from_simple_json()
        self.uncommitted_details = []
        self.uncommitted_history = []

    def get_current_status(self, include_date=False):

        last_event = self.history[0].event
        event_date = self.history[0].readable_date
        if last_event in ('Pending', 'Contingent (Active with Contingency)'):
            state = 'Sale in Progress ({})'.format(last_event)
        elif last_event in ('Sold (MLS) (Sold)',):
            state = 'Sold'
        elif last_event in ('Listed (Active)', 'Relisted (Active)', 'Price Changed'):
            state = 'Active'
        elif 'Delisted' in last_event:
            state = 'Unlisted'
        else:
            state = last_event
        if include_date:
            return '{} - {}'.format(state, event_date)
        else:
            return state

    def add_to_db(self, session):

        session.add(self)
        session.commit()
        self.load_house_details()

        if self.uncommitted_details:
            for hd in self.uncommitted_details:
                session.add(hd)
            session.commit()
            self.uncommitted_details = []

        if self.uncommitted_history:
            for phe in self.uncommitted_history:
                session.add(phe)
            session.commit()
            self.uncommitted_history = []

    def load_from_simple_json(self):

        for key in ('url', 'address', 'price', 'beds', 'baths', 'sqft', 'desc', 'redfinprice'):
            self.__dict__[key] = self.json_data[key]

    def load_house_details(self):

        if not self.id or not self.json_data:
            raise ValueError

        j = self.json_data
        if 'key_details' in j:
            for kd in j['key_details']:
                dj = {'category': 'Key Details', 'key': kd, 'value': j['key_details'][kd], 'house_id': self.id}
                self.uncommitted_details.append(HouseDetail(dj))
        if 'home_facts' in j:
            for hf in j['home_facts']:
                dj = {'category': 'Home Facts', 'key': hf, 'value': j['home_facts'][hf], 'house_id': self.id}
                self.uncommitted_details.append(HouseDetail(dj))
        if 'property_details' in j:
            if 'Property / Lot Details' in j['property_details']:
                if 'Property Information' in j['property_details']['Property / Lot Details']:
                    for pi in j['property_details']['Property / Lot Details']['Property Information']:
                        dj = {'category': 'Property Information', 'key': pi,
                              'value': j['property_details']['Property / Lot Details']['Property Information'][pi],
                              'house_id': self.id}
                        self.uncommitted_details.append(HouseDetail(dj))
            if 'Interior Features' in j['property_details']:
                if 'Room Information' in j['property_details']['Interior Features']:
                    for ri in j['property_details']['Interior Features']['Room Information']:
                        dj = {'category': 'Room Information', 'key': ri,
                              'value': j['property_details']['Interior Features']['Room Information'][ri],
                              'house_id': self.id}
                        self.uncommitted_details.append(HouseDetail(dj))
        if 'property_history' in j:
            d_pattern = '%b %d, %Y'
            for date in j['property_history']:
                dj = {'readable_date': date, 'house_id': self.id, 'event': j['property_history'][date]['event'],
                      'date': int(time.mktime(time.strptime(date, d_pattern)))}
                if 'price' in j['property_history'][date]:
                    dj['price'] = j['property_history'][date]['price']
                self.uncommitted_history.append(PropertyHistoryEvent(dj))


class HouseSet:

    def __init__(self, houses):

        self.houses = houses

    def get_average_price(self):

        num_houses = len(self.houses)
        total_price = 0
        for h in self.houses:
            try:
                total_price += int(h.price.replace(',', '').replace('$', ''))
            except ValueError:
                print "Could not cast {} to int ...".format(h.price)
                num_houses -= 1

        return total_price / float(num_houses)

    def finished_basement_filter(self):

        ret_houses = []

        for h in self.houses:

            for hd in h.details:
                if 'basement' in hd.key.lower():
                    if 'finished' in hd.value.lower() and 'unfinished' not in hd.value.lower():
                        ret_houses.append(h)
                        break

        return HouseSet(ret_houses)


Base.metadata.create_all(engine)


def get_houses(session, status=None):
    q = session.query(RedfinHouse)
    houses = []
    for instance in q:
        if status:
            if instance.get_current_status() == status:
                houses.append(instance)
        else:
            houses.append(instance)
    return houses
