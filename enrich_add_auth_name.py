import requests
import json
import csv
import pymarc
import io
import requests
import string
import unicodedata
from collections import OrderedDict


cache = json.load(open('naco_cache.json'))


def normalize_string(s):
    s = str(s)
    s = s.translate(str.maketrans('', '', string.punctuation))
    s = " ".join(s.split())
    s = s.lower()
    s = s.casefold()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.replace('the','')
    return s

def searchLc(name, title):
	global cache

	if len(cache) % 20 == 0:
		json.dump(cache,open('naco_cache.json','w'))


	d = {}

	if name in cache:
		results = cache[name]
	else:
		# time.sleep(1)
		params = {
			'q' : name,
			'count': 5
		}

		headers={'Accept': 'application/json', 'User-Agent': user_agent}
		url = f"https://id.loc.gov/authorities/names/suggest2/"

		r = requests.get(url,params=params,headers=headers)
		try:
			data = r.json()
		except:
			print("JSON decode error with:",name)
			return None           

		results = data['hits']
		cache[name] = data['hits']
	
	# loop throguh each result and test the name
	for hit in results:
		if normalize_string(hit['suggestLabel']) == normalize_string(name):
			d['author_lccn'] = hit['uri'].split('/')[-1]
			d['author_authorized_heading'] = hit['aLabel']
			return d
	# check the main variant label 
	for hit in results:
		if normalize_string(hit['vLabel']) == normalize_string(name):
			d['author_lccn'] = hit['uri'].split('/')[-1]
			d['author_authorized_heading'] = hit['aLabel']
			return d

	# if there is only one hit and it has unclosed life dates and the name partially matches then select it
	if name[-1] == '-':
		if len(results) == 1:
			if normalize_string(name) in normalize_string(results[0]['aLabel']) or normalize_string(name) in normalize_string(results[0]['vLabel']):
				d['author_lccn'] = hit['uri'].split('/')[-1]
				d['author_authorized_heading'] = hit['aLabel']
				return d

	# if we are here then no match, loop again and look at the titles if enabled

	for hit in results:
		url = 'https://id.loc.gov/resources/works/relationships/contributorto/'
		params = {
			'page': 0,
			'label':hit['aLabel']
		}
		headers={'Accept': 'application/json', 'User-Agent': user_agent}

		r = requests.get(url,params=params,headers=headers)
		try:
			title_data = r.json()
		except:
			print("JSON decode error with:",name)
			return d

		if title_data['results'] != None:
			# convert it to a list if it a single result dictonary
			if type(title_data['results']) != list:
				title_data['results'] = [title_data['results']]
			for title in title_data['results']:
				if normalize_string(title) in normalize_string(title['label']):
					# we found the title hit, use this one
					d['author_lccn'] = hit['uri'].split('/')[-1]
					d['author_authorized_heading'] = hit['aLabel']

					return d

	# often the wrong life dates are used but the main heading part is correct, so keep choping off the end of the heading and check it
	# if we get a hit and then get a title match we can be confident it is correct. but it has to have a least 2 parts
	# for example:
	# "Gorham, Charles O. (Charles Orson), 1911-"
	# "Gorham, Charles O. (Charles Orson)"
	# "Gorham, Charles O. (Charles"
	# "Gorham, Charles O" <- hits a result
	for x in range(len(name.split())-1,1,-1):
		cropped_name = " ".join(name.split()[0:x])
		if cropped_name[-1] == '.'  or cropped_name[-1] == ',':
			cropped_name = cropped_name[:-1]
		

		params = {
			'q' : cropped_name,
			'count': 5
		}
		headers={'Accept': 'application/json', 'User-Agent': user_agent}
		url = f"https://id.loc.gov/authorities/names/suggest2/"

		r = requests.get(url,params=params,headers=headers)
		try:
			data = r.json()
		except:
			print("JSON decode error with:",name)
			return None
		
		if len(data['hits']) == 0:
			return None

		results = data['hits']
		for hit in results:
			url = 'https://id.loc.gov/resources/works/relationships/contributorto/'
			params = {
				'page': 0,
				'label':hit['suggestLabel']
			}
			headers={'Accept': 'application/json', 'User-Agent': user_agent}

			r = requests.get(url,params=params,headers=headers)
			try:
				title_data = r.json()
			except:
				print("JSON decode error with:",name)
				return None

			if title_data['results'] != None:
				# convert it to a list if it a single result dictonary
				if type(title_data['results']) != list:
					title_data['results'] = [title_data['results']]
				for title in title_data['results']:
					if normalize_string(title) in normalize_string(title['label']):
						# we found the title hit, use this one
						d['author_lccn'] = hit['uri'].split('/')[-1]
						d['author_authorized_heading'] = hit['aLabel']
						print("Found",name,"using cropped", cropped_name)
						return d








files = ['doubleday.csv','harper_collins.csv','macmillan.csv','random_house.csv','simon_schuster.csv']
user_agent = "Test Script - Matt."


counter = 0	
for file in files:
	
	output_dicts = []	
	with open(file) as infile:


		reader = csv.DictReader(infile)

		for row in reader:

			counter+=1

			print(row['oclc'], " | ", counter)

			title = row['title'].split("/")[0].split(":")[0].strip()
			marc_file = open(f'marc/{row["oclc"]}.xml')
			marc = marc_file.read()
			marc_file.close()

			row['author_lccn']=None
			row['author_authorized_heading']=None

			with io.StringIO() as f:
				f.write(marc)
				f.seek(0)

				try:
					record = pymarc.marcxml.parse_xml_to_array(f)[0]
				except:
					print("Bad MARC:", marc)
					output_dicts.append(row)
					continue

				field = None
				if '100' in record:
					field = record['100']
				elif '110' in record:
					field = record['110']
				elif '111' in record:
					field = record['111']
				elif '700' in record:
					field = record['700']
				elif '710' in record:
					field = record['710']
				elif '711' in record:
					field = record['711']                                
				else:
					print("No Author found!:", marc)
					output_dicts.append(row)
					continue

				# assbel the heading in the correct order 
				name = field['a']
				if 'b' in field:
					name = name + ' ' + field['b']
				if 'c' in field:
					name = name + ' ' + field['c']
				if 'q' in field:
					name = name + ' ' + field['q']                  
				if 'd' in field:
					name = name + ' ' + field['d']   
				if 'g' in field:
					name = name + ' ' + field['g']   
	 
				# have seen empty "" 100 fields
				if len(name.strip()) == 0:
					print("No Author found!:", marc)
					output_dicts.append(row)
					continue

				# remove the optional trailing period on all headings if there
				if name[-1] == '.':
					name = name[:-1]
				if name[-1] == ',':
					name = name[:-1]


				print(name)  
				print(title)


				searchLc_result = searchLc(name,title)
				if searchLc_result != None:
					row['author_lccn'] = searchLc_result['author_lccn']
					row['author_authorized_heading'] = searchLc_result['author_authorized_heading']

				output_dicts.append(row)


				print(searchLc_result)
				# data['name_authority'] = searchLc_result


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
			('author_authorized_heading',None)
		]))
		writer.writeheader()

		for row in output_dicts:
			writer.writerow(row)


