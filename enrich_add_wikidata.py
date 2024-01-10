import requests
import json
import csv
import pymarc
import io
import requests
import string
import unicodedata
from collections import OrderedDict
import urllib.parse


properties = json.load(open('wikidata_properties.json'))
plabels = {}
pcount = {}
for p in properties:
	pid = p['property'].split("/")[-1]
	plabels[pid] = p['propertyLabel']


labelcache = {}


def get_label(qid):
	global labelcache
	if qid in labelcache:
		return labelcache[qid]

	response = requests.get(f"https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids={qid}&languages=en&format=json")

	try:
		labelcache[qid] = response.json()['entities'][qid]['labels']['en']['value']
		return labelcache[qid]

	except: 
		return qid


headers = {
	'Accept' : 'application/json',
	'User-Agent': "user:thisismattmiller - data job"
}

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

			row['wikipedia']=None
			row['wikipedia_categories'] = None
			row['wikidata_gender'] = None
			row['wikidata_country'] = None
			row['wikidata_ethnic_group'] = None
			row['wikimedia_image'] = None

			if row['author_wikidata'] != "":

				r = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{row['author_wikidata']}.json")

				data = r.json()

				wikidata = {
					'meta': data['entities'][row['author_wikidata']],
					'categories' : None,
					'title': None
				}		

				if 'enwiki' in data['entities'][row['author_wikidata']]['sitelinks']:

					page_title = data['entities'][row['author_wikidata']]['sitelinks']['enwiki']['url'].split("/")[-1]
					r = requests.get(f"https://en.wikipedia.org/w/api.php?format=json&action=query&prop=categories&titles={page_title}",headers=headers)
					catagories = r.json()
					catagories = catagories['query']['pages']
					catagories = catagories[list(catagories.keys())[0]]['categories']
					wikidata['title'] = page_title
					wikidata['categories'] = catagories


				wiki_d = {
					'qid' : None,
					'gender' : None,
					'country' : None,
					'ethnic_group':None,
					'image' : None,
					'categories' : None,
					'wikipedia': None
				}	


				row['wikipedia'] = f"https://en.wikipedia.org/wiki/{wikidata['title']}"

				categories = []
				if wikidata['categories'] != None:
					for c in wikidata['categories']:
						categories.append(c['title'].split('Category:')[1])

				row['wikipedia_categories'] = "|".join(categories)


				for p in wikidata['meta']['claims']:
					claim = wikidata['meta']['claims'][p]
					# print(plabels[p])
					l = f"{plabels[p]} ({p})"
					if l not in pcount:
						pcount[l] = 0

					pcount[l]=pcount[l]+1

					if p == 'P21':

						# print(json.dumps(claim,indent=2))
						if 'datavalue' in claim[0]['mainsnak']:

							gender_qid = claim[0]['mainsnak']['datavalue']['value']['id']
							gender_label = get_label(gender_qid)

							row['wikidata_gender'] = gender_label
						
							# print(gender_label)


					if p == 'P27':
						countries = []
						for c in claim:

							if 'datavalue' in c['mainsnak']:
								country_qid = c['mainsnak']['datavalue']['value']['id']

								countries.append(get_label(country_qid))

						row['wikidata_country'] = "|".join(countries)


					if p == 'P172':
						ethnic_group = []
						for c in claim:

							if 'datavalue' in c['mainsnak']:
								e_qid = c['mainsnak']['datavalue']['value']['id']

								ethnic_group.append(get_label(e_qid))

						row['wikidata_ethnic_group'] = "|".join(ethnic_group)

					if p == 'P18':


						imageurl = 'https://commons.wikimedia.org/wiki/File:' + urllib.parse.quote(claim[0]['mainsnak']['datavalue']['value'], safe="")
						row['wikimedia_image'] = imageurl




			
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
			('author_wikidata_url',None),
			('wikipedia',None),
			('wikipedia_categories',None),
			('wikidata_gender',None),						
			('wikidata_country',None),
			('wikidata_ethnic_group',None),
			('wikimedia_image',None)														

		]))
		writer.writeheader()

		for row in output_dicts:
			writer.writerow(row)

	



