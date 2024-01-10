import requests
import json
import csv
import pymarc
import io
import requests
import string
import unicodedata
from collections import OrderedDict


def chunks(lst, n):
	"""Yield successive n-sized chunks from lst."""
	for i in range(0, len(lst), n):
		yield lst[i:i + n]

def normalize_string(s):
	s = str(s)
	s = s.translate(str.maketrans('', '', string.punctuation))
	s = " ".join(s.split())
	s = s.lower()
	s = s.casefold()
	s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
	s = s.replace('the','')
	return s



files = ['doubleday.csv','harper_collins.csv','macmillan.csv','random_house.csv','simon_schuster.csv']


counter = 0	
for file in files:
	
	output_dicts = []	
	all_lccns = []
	with open(file) as infile:


		reader = csv.DictReader(infile)
		

		for row in reader:

			counter+=1
			print(row['oclc'], " | ", counter)

			if row['author_lccn'] != "":
				all_lccns.append(row['author_lccn'])


	lccn_to_wiki = {}

	for c in chunks(all_lccns,250):


		sparql = f"""
			SELECT ?item ?lccns
			WHERE 
			{{
			  
			  VALUES ?lccns {{ {' '.join('"{0}"'.format(l) for l in c)} }} .
			  
			  ?item wdt:P244 ?lccns .


			}}
		"""


		params = {
			'query' : sparql
		}

		headers = {
			'Accept' : 'application/json',
			'User-Agent': "user:thisismattmiller - data job"
		}
		url = "https://query.wikidata.org/sparql"


		r = requests.get(url, params=params, headers=headers)

		data = r.json()

		# did we get any results
		for row in data['results']['bindings']:


			lccn_to_wiki[row['lccns']['value']] = row['item']['value'].split("/")[-1]



	with open(file) as infile:

		reader = csv.DictReader(infile)

		for row in reader:

			counter+=1
			print(row['oclc'], " | ", counter)

			if row['author_lccn'] != "":
				if row['author_lccn'] in lccn_to_wiki:
					row['author_wikidata'] = lccn_to_wiki[row['author_lccn']]
					row['author_wikidata_url'] = f"https://wikidata.org/entity/{lccn_to_wiki[row['author_lccn']]}"

			output_dicts.append(row)

	with open(file,'w') as outfile:

		writer = csv.DictWriter(outfile, fieldnames=OrderedDict([
			('rank',None),
			('oclc',None),
			('link',None),
			('isbns',None),
			('title',None),
			('date',None),
			('creator',None),
			('publishers',None),
			('genres',None),
			('author_lccn',None),
			('author_authorized_heading',None),
			('author_wikidata',None),
			('author_wikidata_url',None)
			

		]))
		writer.writeheader()

		for row in output_dicts:
			writer.writerow(row)

	






