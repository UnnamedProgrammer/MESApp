import datetime as dt
from datetime import timedelta

def makedate(start, end):
    datelist = []
    if(start == "7:00" and end == "19:00"):
        startd = dt.datetime.strptime(start, "%H:%M")
        endd = dt.datetime.strptime(end, "%H:%M") 
    else:
        startd = dt.datetime.strptime(start, "%H:%M")
        endd = dt.datetime.strptime(end, "%H:%M")+timedelta(days=1)

    while(startd != endd):
        datelist.append(startd)
        startd = startd + timedelta(minutes=1)
        print(startd)
    return datelist

makedate("19:00","7:00")