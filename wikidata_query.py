import os
import json
import hashlib
import requests
import urllib
import datetime
import matplotlib.pyplot as plt

class WikimediaFetcher(object):
    def __init__(self):
        self.queries_cache_dir = 'queries_cache'
        if not os.path.exists(self.queries_cache_dir):
            os.makedirs(self.queries_cache_dir)


    def hash_string(self, s):
        return hashlib.md5(s.encode('utf-8')).hexdigest()


    def run_query(self, query):
        query = urllib.parse.quote(query)
        cmd = 'https://query.wikidata.org/sparql?format=json&query={}'.format(query)
        filename = os.path.join(self.queries_cache_dir, '{}.json'.format(self.hash_string(cmd)))
        if os.path.exists(filename):
            with open(filename, 'r') as data_file:
                return json.load(data_file)
        results = requests.get(cmd).json()
        with open(filename, 'w') as data_file:
            json.dump(results, data_file)
        return results


class PresidentsStats(object):
    def __init__(self):
        pass


    def get_dates_data(self):
        q = '''
SELECT ?presLabel ?pres ?start_date ?end_date ?birth_date ?death_date WHERE {
  ?pres wdt:P31 wd:Q5 .
  ?pres p:P39 ?presidency_statement .
  ?presidency_statement ps:P39 wd:Q11696 .
  ?presidency_statement pq:P580 ?start_date .
  OPTIONAL { ?presidency_statement pq:P582 ?end_date . }
  ?pres wdt:P569 ?birth_date .
  OPTIONAL { ?pres wdt:P570 ?death_date . }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
ORDER BY ?start_date
'''
    
        wf = WikimediaFetcher()
        results = wf.run_query(q)
        return results


    def create_timeline(self):
        '''timeline of how many living presidents or ex-presidents there are.'''
        timeline = []
        results = self.get_dates_data()
        for r in results['results']['bindings']:
            #print(r)
            start_date = r['start_date']['value']
            timeline.append([start_date, 1])
            if 'death_date' in r:
                death_date = r['death_date']['value']
                timeline.append([death_date, -1])
        timeline.sort(key=lambda x: x[0])
        cum = 0
        c_timeline = []
        for t in timeline:
            #print(t)
            moment = datetime.datetime.strptime(t[0], '%Y-%m-%dT%H:%M:%SZ')
            c_timeline.append([moment - datetime.timedelta(seconds=1), cum])
            cum += t[1]
            c_timeline.append([moment, cum])
            #c_timeline.append([t[0], cum])
            #print('--->', c_timeline[-1])
        return c_timeline


    def plot_graph(self):
        timeline = ps.create_timeline()
        #print(timeline)
        #x = [datetime.datetime.strptime(s[0], '%Y-%m-%dT%H:%M:%SZ') for s in timeline]
        x = [s[0] for s in timeline]
        y = [s[1] for s in timeline]
        #print(x)
        #print(y)
        plt.plot(x, y)
        plt.show()


if __name__ == '__main__':
    ps = PresidentsStats()
    ps.plot_graph()
