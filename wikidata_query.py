import os
import json
import hashlib
import requests
import urllib
import matplotlib.pyplot as plt
import pandas as pd

class WikidataFetcher(object):
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


    def dataframe_query(self, query):
        results = self.run_query(query)
        columns = results['head']['vars']
        rows = [[res.get(col) and res[col]['value'] for col in columns] for res in results['results']['bindings']]
        d = [{col: res.get(col) and res[col]['value'] for col in columns} for res in results['results']['bindings']]
        df = pd.DataFrame(d)
        return df


class PresidentsStats(object):
    def __init__(self):
        self.query = '''
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


    def get_dataframe(self):
        wf = WikidataFetcher()
        df = wf.dataframe_query(self.query)

        df = pd.melt(df, id_vars=['pres', 'presLabel'], var_name='event', value_name='date')
        df = df.sort_values(by=['date'])
        return df


    def event_to_num(self, row):
        if row['event'] in ['birth_date', 'end_date']:
            return 0
        if row['event'] == 'start_date':
            return 1
        if row['event'] == 'death_date':
            return -1


    def get_dates_data(self):
        df = ps.get_dataframe()
        df = df[['presLabel', 'date', 'event']]
        df = df[df['date'].notnull()]
        df['change'] = df.apply(self.event_to_num, axis=1)
        df['total_number'] = df['change'].cumsum(axis=0)
        return df


    def plot_graph(self):
        df = ps.get_dates_data()
        df.plot(x='date', y='total_number', drawstyle='steps', legend=False)
        plt.show()


if __name__ == '__main__':
    ps = PresidentsStats()
    ps.plot_graph()
