# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 16:12:24 2022

@author: ie20391
"""

class edgar_data:
    '''
    To extract data from EDGAR SEC to python dictionary. Attributes of class are:
        - submissions_url - to show link to submissions;
        - data_url - to show link to EDGAR facts;
        - about_company - dict with information about a company;
        - available_data - pd.DataFrame with company's reports;
        - facts - the facts dictionary from EDGAR SEC;
    '''
    
    def __init__(self, company, hdr):
        #cik needs to be of len 10
        self.hdr = hdr
        if type(company) == str:
            self.ticker = company
            self.cik = edgar_data.find_cik(self)
        else:
            self.cik = company
        if len(str(self.cik)) < 10:
                self.cik = str('CIK' + ('0'*(10-len(str(self.cik))))+str(self.cik))
        else:
            raise ValueError('Non-parsable CIK')
        if self.hdr['user-agent'] == None:
            raise ValueError('''Please, specify user-agent requirements, as described in:
                                 
                                 https://www.sec.gov/os/accessing-edgar-data
                                 
                             ''')
        
        self.submissions_url = f"https://data.sec.gov/submissions/{self.cik}.json"
        self.data_url = f'https://data.sec.gov/api/xbrl/companyfacts/{self.cik}.json'
        self.about_company = edgar_data.company_info(self)
        self.available_data = edgar_data.library(self)
        self.facts = edgar_data.access_facts(self)
        
    
    def find_cik(self):
        import requests
        
        ciks_all = requests.get('https://www.sec.gov/files/company_tickers.json',
                                headers = self.hdr).json()
        ciks_all = dict([(val['ticker'], val['cik_str']) for key, val in ciks_all.items()])
        return ciks_all[self.ticker]
    
    def library(self):
        import json
        import requests
        import pandas as pd
        data = json.loads(requests.get(self.submissions_url, headers = self.hdr)._content.decode('utf8'))
        #if there are old filings available, then return df containing all finlings
        if len(data['filings']['files']) !=0:
            prior_submission_number = data['filings']['files'][0]['name']
            old_data = json.loads(requests.get(f'https://data.sec.gov/submissions/{prior_submission_number}',headers = self.hdr
                                               )._content.decode('utf8'))
            df = pd.DataFrame(data = {'rep_date':data['filings']['recent']['reportDate'] + old_data['reportDate'],
                                      'filling_date':data['filings']['recent']['filingDate'] + old_data['filingDate'],
                                      'form':data['filings']['recent']['form'] + old_data['form'],
                                      'xbrl':data['filings']['recent']['isXBRL'] + old_data['isXBRL'],
                                      'accession_num':data['filings']['recent']['accessionNumber'] + old_data['accessionNumber']})
            df = df[((df.form == '10-K') | (df.form == '10-Q')) & (df.xbrl == 1)].sort_values(by = ['rep_date'])
            df.index = [i for i in range(len(df))]
            return df
        else:
            df = pd.DataFrame(data = {'rep_date':data['filings']['recent']['reportDate'],
                                'filling_date':data['filings']['recent']['filingDate'],
                              'form':data['filings']['recent']['form'],
                              'xbrl':data['filings']['recent']['isXBRL'],
                              'accession_num':data['filings']['recent']['accessionNumber']})
        
            df = df[((df.form == '10-K') | (df.form == '10-Q')) & (df.xbrl == 1)].sort_values(by = ['rep_date'])
            df.index = [i for i in range(len(df))]
            return df
    
    def company_info(self):
        import json
        import requests
        data = json.loads(requests.get(self.submissions_url, headers = self.hdr)._content.decode('utf8'))
        d = {}
        if len(data['tickers']) > 0:    
            d['ticker'] = data['tickers'][0]
        else:
            d['ticker'] = None
        if len(data['name']) > 0:
            d['name'] = data['name']
        else:
            d['name'] = None
        if len(data['sic']) > 0:
            d['sic'] = data['sic']
        else:
            d['sic'] = None
        if len(data['sicDescription']) > 0:
            d['sic_descr'] = data['sicDescription']
        else:
            d['sic_descr'] = None
        return d
        
        
    def access_facts(self):
        import json
        import requests
        
        data = json.loads(requests.get(self.data_url, headers = self.hdr)._content.decode('utf8'))
        keys = list(data['facts'].keys())
        
        if 'us-gaap' in keys and 'ifrs-full' in keys:
            if len(data['facts']['us-gaap']) > len(data['facts']['ifrs-full']):
                data = data['facts']['us-gaap']
            else:
                data = data['facts']['ifrs-full']
            return data
        elif 'us-gaap' in keys and 'ifrs-full' not in keys:
            return data['facts']['us-gaap']
        elif 'us-gaap' not in keys and 'ifrs-full' in keys:
            return data['facts']['ifrs-full']
        
if __name__ == '__main__':
    edgar_data