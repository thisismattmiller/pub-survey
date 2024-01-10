import requests
import json
import csv
from collections import OrderedDict


response = requests.post(
	'https://oauth.oclc.org/token',
	data={"grant_type": "client_credentials", 'scope': ['wcapi']},
	auth=('OCLC_CLIENT_ID', 'OCLC_SECRET'),
)

print(response.text)
token = response.json()["access_token"]

url = 'https://americas.discovery.api.oclc.org/worldcat/search/v2/bibs'
counter=0


files = {
	'doubleday.csv':'Doubleday',
	'harper_collins.csv': 'HarperCollins',
	'macmillan.csv': 'Macmillan',
	'random_house.csv': 'Random House',
	'simon_schuster.csv': 'Simon & Schuster'
}


for file in files:

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
			('genres',None)

		]))
		writer.writeheader()

		for offset in range(0,1000,50):
			print(offset)
			
			offset = offset + 1


			params = {
				'q' : f'pb:{files[file]}',
				'datePublished': ['2019', '2020', '2021', '2022','2023'],
				'inLanguage': ['eng'],
				'itemType': ['book'],
				'content' : ['fic'],
				'audience' : 'nonJuv',
				'orderBy':'mostWidelyHeld',
				'limit' : 50,
				'offset': offset

			}

			headers = {
				'accept': 'application/json',
				'Authorization': f'Bearer {token}'
			}


			response = requests.get(url,params=params,headers=headers)

			data = response.json()
			print(data)
			for record in data['bibRecords']:
				counter=counter+1

				row = {'rank':counter}
				print(json.dumps(record,indent=2))
				row['oclc'] = record['identifier']['oclcNumber']
				row['link'] = f"https://search.worldcat.org/title/{row['oclc']}"
				if 'isbns' in record['identifier']:
					row['isbns'] = "|".join(record['identifier']['isbns'])
				
				row['title'] = record['title']['mainTitles'][0]['text']
				creators = []
				if 'contributor' in record:

					if 'creators' in record['contributor']:

						for c in record['contributor']['creators']:
							
							if 'firstName' in c:
								name = c['firstName']['text']
								if 'secondName' in c:
									json.dumps(c,indent=2)
									if 'text' in c['secondName']:
										name = name + ' ' + c['secondName']['text']


								creators.append( name )
							elif 'nonPersonName' in c:
								creators.append(c['nonPersonName']['text'])
					else:
						if 'statementOfResponsibility' in record['contributor']:
							creators.append(record['contributor']['statementOfResponsibility']['text'])
						
				row['creator'] = "|".join(creators)

				publishers = []
				if 'publishers' in record:					
					for c in record['publishers']:
						publishers.append(c['publisherName']['text'])
				row['publishers'] = "|".join(publishers)

				genres = []
				if 'genres' in record['description']:
					for c in record['description']['genres']:
						genres.append(c)


				row['genres'] = "|".join(genres)


				row['date'] = record['date']['machineReadableDate']
				

				print(row)

				writer.writerow(row)


			# if offset >= 100:
			# 	break
		