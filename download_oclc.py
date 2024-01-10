import requests
import json
import csv
import os.path

files = ['doubleday.csv','harper_collins.csv','macmillan.csv','random_house.csv','simon_schuster.csv']

counter = 0	
for file in files:
	
	with open(file) as infile:

		reader = csv.DictReader(infile)

		for row in reader:

			counter+=1

			

			if os.path.isfile(f"marc/{row['oclc']}.xml") == True:
				continue

			print(row['oclc'], " | ", counter)
			url = f"https://www.worldcat.org/webservices/catalog/content/{row['oclc']}?wskey=YOUR_WSKEY"

			response = requests.get(url)

			with open(f"marc/{row['oclc']}.xml",'w') as out:
				out.write(response.text)
			

