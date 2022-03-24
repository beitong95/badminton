'''
1. autotomatically book the most recent timeslots
2. repeatly building btninfo object problem
3. use MQTT to warn the user that the cookie is invalid
4. remote control: SSH, VNC
Don't login to ARC's website on multiple machines

'''


########################################################################

import requests
import json
from pycookiecheat import chrome_cookies
from metaDataBadminton import metaDataBadminton
import datetime
import re
import time
import argparse
from random import randrange
#########################################################################
# setting
bookingId = metaDataBadminton["bookingId"]
courtIds = list(metaDataBadminton["court"])
today = datetime.datetime.now().day # today's day
month_today = datetime.datetime.now().month # today's month
three_days = datetime.timedelta(days=3)
day = (datetime.datetime.now() + three_days).day
month = (datetime.datetime.now() + three_days).month
year = datetime.datetime.now().year
dateStr = "/" + str(year) + "/" + str(month) + "/" + str(day)

# 10182021 add argument parser
parser = argparse.ArgumentParser(description='Badminton. If I prefer to book court 2 for 3-4pm. The command is: python badminton.py -c 2 -t 3')
parser.add_argument('-c', type=int,
                    help='Which court do you prefer to book? {1,2,3,4}. Default: A random court', default=randrange(1,5), nargs='?')
parser.add_argument('-t', type=int,
                    help='Which time slot do you prefer to book? {2,3,4,5,6,7,8}. Default: The cloest timeslot', default=datetime.datetime.now().hour+1 - 12, nargs='?')
args = parser.parse_args()

# court 1,2,3,4 or any; default: any
# currently the user can only  specify one timeSlot
# start time 1-8 pm 10-12 am; PLEASE use the left part
'''
"10-11": "10 - 11 AM",
"11-12": "11 AM - 12 PM",
"12-1": "12 - 1 PM",
"1-2": "1 - 2 PM",
"2-3": "2 - 3 PM",
"3-4": "3 - 4 PM",
"4-5": "4 - 5 PM",
"5-6": "5 - 6 PM",
"6-7": "6 - 7 PM",
"7-8": "7 - 8 PM",
"8-9": "8 - 9 PM"
'''
court = str(args.c)
timeSlot = str(args.t) + '-' + str(args.t + 1)

# bot time setting; unit second; make sure it is smaller than 60 seconds
before = 5.0 # bot starts to work 5 s ahead of the opentime
after = 5.0 # bot keeps working 5 s after the opentime
requestInterval = 0.5 # the smaller the more aggressive
retryInterval = 0.1 # the smaller the more aggressive
waitInterval = 3 # wait interval before the bot starts to work
cookieAddress = "/Users/beitongtian/Library/ApplicationSupport/Google/Chrome/Profile 1/Cookies"
# setting ends
##########################################################################

#extract start time
startTime = int(timeSlot.split('-')[0])
#get string for latter pattern matching
clue = metaDataBadminton['clue'][str(startTime)]
#create booking open date obj
if startTime <= 8:
    startDateHour = 12 + startTime
else:
    startDateHour = startTime
startDate = datetime.datetime(year,month_today,today,startDateHour, 0,0)

# We use request to get the timeslotId, apt-id and timeslotinstance=id
btnInfo = {}


for i in courtIds:
    btnInfo[i] = {}
    btnInfo[i]["courtId"] = metaDataBadminton["court"][i]
    btnInfo[i]["requestUrl"] = "https://active.illinois.edu/booking/" + bookingId + "/slots/" + btnInfo[i]["courtId"] + dateStr

def testTime(t):
    timeDiff = t - startDate
    secondDiff = timeDiff.total_seconds()
    if secondDiff > -before and secondDiff < after:
        return True
    else:
        return False
"""
print(testTime(datetime.datetime(year,month,day, 9,59,59)))
print(testTime(datetime.datetime(year,month,day, 10,0,1)))
print(testTime(datetime.datetime(year,month,day, 10,0,11)))
print(testTime(datetime.datetime(year,month,day, 9,59,49)))
"""


def startReserve(court, cookies):
    data = {
        'bId': bookingId,
        'fId': btnInfo[court]["courtId"],
        'aId': btnInfo[court]["apt-id"],
        'tsId': btnInfo[court]["timeslot-id"],
        'tsiId': btnInfo[court]["timeslotinstance-id"],
        'y': year,
        'm': month,
        'd': day,
        't': '',
        'v': 0
    }
    print("Trying to book court: " + court + " on " + dateStr + " timeSlot: " + timeSlot)
    print("Post data: ", data)

    response = requests.post('https://active.illinois.edu/booking/reserve', data=data, cookies=cookies)

    print("Booking result: " + response.text)
    if '"Success":true' in response.text:
        print("Booking Success", datetime.datetime.now())
        return True
    else:
        return False


cookieUrl = "https://active.illinois.edu/booking/reserve"
booked = False

# wait till the booking time
while True:
    time.sleep(waitInterval)
    requests_cookies = chrome_cookies(cookieUrl, cookie_file=cookieAddress)
    r = requests.get(btnInfo['court1']["requestUrl"], cookies=requests_cookies)
    if "booking-slot-item" in r.text:
        print("The cookie is valid")
    else:
        print("The cookie is not valid any more. Please re-login your UIUC account")
    currentTime = datetime.datetime.now()
    print("CurrentTime:", currentTime, "Booking Open Time:", startDate, "Reserving", dateStr[1:] , "Time Slot:", timeSlot, "Court:", court)
    if testTime(currentTime):
        break
    else: 
        print("Waiting. Current waiting interval is: ", str(waitInterval), "request interval is: ", str(requestInterval))
        continue

print("Pass time checking. Wake up Bot. Bot starts working.")

while not booked and testTime(datetime.datetime.now()): 
    # try the prefered timeslot
    time.sleep(requestInterval)
    requests_cookies = chrome_cookies(cookieUrl, cookie_file=cookieAddress)
    c = 'court' + court
    r = requests.get(btnInfo[c]["requestUrl"], cookies=requests_cookies)
    # check if the cookie is valid
    if "data-apt-id" in r.text:
        newr = r.text.split('\r\n') #parse html file
        
        # locate info we will use
        findTime = False
        for i, line in enumerate(newr):
            # if we find the exact time we want
            if clue in line:
                baseLineNum = i
                findTime = True
                break
        # if we cannot find the info we need, we will check the next court
        if findTime == False:
            continue # go to line 203

        print("Printing information we need...")
        line1 = newr[baseLineNum-1]
        print(line1)
        line2 = newr[baseLineNum]
        print(line2)

        # extract info: apt-id, timeslot-id, timeslotinstance-id
        try:
            found = re.search('data-apt-id="(.+?)"', line1).group(1) 
            print(found)
        except AttributeError:
            found = ''
            continue # pass this court if we cannot extract the correct infomation

        btnInfo[c]["apt-id"] = found 

        try:
            found = re.search('data-timeslot-id="(.+?)"', line1).group(1) 
            print(found)
        except AttributeError:
            found = ''
            continue # pass this court if we cannot extract the correct infomation

        btnInfo[c]["timeslot-id"] = found

        try:
            found = re.search('data-timeslotinstance-id="(.+?)"', line2).group(1) 
            print(found)
        except AttributeError:
            found = ''
            continue # pass this court if we cannot extract the correct infomation

        btnInfo[c]["timeslotinstance-id"] = found

        print("Successfully get all info we need to book a court. Now Booking...")

        if startReserve(c, requests_cookies):
            booked = True
            break # if we successfully booked a court we quit
        else: 
            time.sleep(retryInterval)
    else: 
        print("Booking information has not been updated", datetime.datetime.now())
        continue
    # If we arrive here, it means we cannot book our preferred court. We try other courts. 
    # for each court get its btn info
    for c in btnInfo:
        if c == ('court' + court): # skip the preferred court
            continue
        r = requests.get(btnInfo[c]["requestUrl"], cookies=requests_cookies)
        # check if the cookie is valid
        if "data-apt-id" in r.text:
            newr = r.text.split('\r\n') #parse html file
            
            # locate info we will use
            findTime = False
            for i, line in enumerate(newr):
                # if we find the exact time we want
                if clue in line:
                    baseLineNum = i
                    findTime = True
                    break
            # if we cannot find the info we need, we will check the next court
            if findTime == False:
                continue

            print("Printing information we need...")
            line1 = newr[baseLineNum-1]
            print(line1)
            line2 = newr[baseLineNum]
            print(line2)

            # extract info: apt-id, timeslot-id, timeslotinstance-id
            try:
                found = re.search('data-apt-id="(.+?)"', line1).group(1) 
                print(found)
            except AttributeError:
                found = ''
                continue # pass this court if we cannot extract the correct infomation

            btnInfo[c]["apt-id"] = found 

            try:
                found = re.search('data-timeslot-id="(.+?)"', line1).group(1) 
                print(found)
            except AttributeError:
                found = ''
                continue # pass this court if we cannot extract the correct infomation

            btnInfo[c]["timeslot-id"] = found

            try:
                found = re.search('data-timeslotinstance-id="(.+?)"', line2).group(1) 
                print(found)
            except AttributeError:
                found = ''
                continue # pass this court if we cannot extract the correct infomation

            btnInfo[c]["timeslotinstance-id"] = found

            print("Successfully get all info we need to book a court. Now Booking...")

            if startReserve(c, requests_cookies):
                booked = True
                break # if we successfully booked a court we quit
            else: 
                time.sleep(retryInterval)  # if fail we go to next court
        else: 
            print("Booking information has not been updated", datetime.datetime.now())
            continue

print("Script finished! Go to Arc website to check the result")



