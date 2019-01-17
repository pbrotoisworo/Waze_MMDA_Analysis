from bs4 import BeautifulSoup
import csv
from time import sleep, asctime
from dateutil.parser import parse
from datetime import datetime, timedelta
import urllib.request

print(f'Waze XML Parser (Build 10282018)\nContact: panji.p.broto@gmail.com\n')
print(f'Fetching Waze data...\n')

# get url
with open('wazeURL.txt', 'r') as txt:
    for x in txt:
        wazeURL = x

# never ending loop
stopLoop = False
while stopLoop == False:

    userConnection = False
    while userConnection == False:

        try:
            wazeFeed = urllib.request.urlopen(wazeURL).read()
            userConnection = True
        except:
            print('CONNECTION ERROR. Trying again in 15 seconds')
            sleep(15)

    soup = BeautifulSoup(wazeFeed, 'xml')

    lstDuplicateCheck = []
    with open('waze_feed.csv', 'r', newline='') as csvFile:
        reader = csv.reader(csvFile)
        for idx, row in enumerate(reversed(list(csvFile))):
            lstDuplicateCheck.append(row.split(',')[1])
            if idx == 500:
                break

    itemCounter = 0

    for item in soup.find_all('item'):
        if item.title.text == 'alert' and item.type.text == 'ACCIDENT':
            xmlID = item.uuid.text
            xmlTitle = item.title.text

            xmlTimestamp = item.pubDate.text
            xmlTimestamp = str(parse(xmlTimestamp))
            xmlTimestamp = xmlTimestamp.split('+')[0]
            xmlTimestamp = datetime.strptime(xmlTimestamp, "%Y-%m-%d %H:%M:%S")
            xmlTimestamp = xmlTimestamp + timedelta(hours=8)

            try:
                xmlCity = item.city.text
            except AttributeError:
                pass

            try:
                xmlStreet = item.street.text
            except AttributeError:
                pass

            xmlLat = item.point.text.split(' ')[0]
            xmlLong = item.point.text.split(' ')[1]
            xmlType = item.type.text
            xmlSubtype = item.subtype.text
            xmlConfidence = item.confidence.text
            xmlReliability = item.reliability.text

            dictCombined = {'Timestamp': xmlTimestamp, 'Unique ID': xmlID, 'Title': xmlTitle, 'City': xmlCity, 'Street': xmlStreet,
                            'Latitude': xmlLat, 'Longitude': xmlLong, 'Type': xmlType, 'Subtype': xmlSubtype,
                            'Confidence': xmlConfidence, 'Reliability': xmlReliability}
            dictKeys = dictCombined.keys()

            try:
                if xmlID not in lstDuplicateCheck:
                    print(f'Unique ID: {xmlID}')
                    print(f'Title: {xmlTitle}')
                    print(f'Timestamp: {xmlTimestamp}')
                    print(f'City: {xmlCity}')
                    print(f'Street: {xmlStreet}')
                    print(f'Latitude: {xmlLat}')
                    print(f'Longitude: {xmlLong}')
                    print(f'Type: {xmlType}')
                    print(f'Subtype: {xmlSubtype}')
                    print(f'Confidence: {xmlConfidence}')
                    print(f'Reliability: {xmlReliability}\n')
                    itemCounter += 1
                    try:
                        with open('waze_feed.csv', 'a', newline='') as csvFile:
                            dict_writer = csv.DictWriter(csvFile, dictKeys)
                            dict_writer.writerow(dictCombined)
                    except UnicodeError:
                        with open('waze_feed.csv', 'a', encoding='utf-8', newline='') as csvFile:
                            dict_writer = csv.DictWriter(csvFile, dictKeys)
                            dict_writer.writerow(dictCombined)

            except PermissionError:
                print('Error! CSV file is open. Close CSV file and run script again.')
                input('Press ENTER to continue.')

    if itemCounter > 0:
        print(f'Parsed {itemCounter} new items')
        print('Next refresh in 10 minutes')
        print(f'Current time: {asctime()}\n')

    else:
        print('No new data! Next refresh in 10 minutes')
        print(f'Current time: {asctime()}\n')

    sleep(600)
