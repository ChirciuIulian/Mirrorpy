# smart mirror

from Tkinter import *
import pickle
import locale
import threading
import requests
import time
import json
import traceback
import feedparser
import datetime
import os.path
import dateutil.parser

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from PIL import Image, ImageTk
from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()

ip = '192.168.1.106'
ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = 24 # 12 or 24
date_format = "%d %b, %Y" 
news_country_code = 'ro'

weather_api_token = '3b4d0d837c0b09ab6226c510aafdec75' # key de pe https://darksky.net/dev/
weather_lang = 'ro' # https://darksky.net/dev/docs/forecast pentru lista de limbi
weather_unit = 'ca' # https://darksky.net/dev/docs/forecast pentru lista de unitati de masura
latitude = '45.38'  
longitude = '25.35' 

xlarge_text_size = 100
large_text_size = 54
medium_text_size = 34
small_text_size = 18

@contextmanager
def setlocale(name): #thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

# icons pentru meteo
icon_lookup = {
    'clear-day': "logo/Sun.png",  # soare
    'wind': "logo/Wind.png",   #vant
    'cloudy': "logo/Cloud.png",  # innorat
    'partly-cloudy-day': "logo/PartlySunny.png",  # partial innorat
    'rain': "logo/Rain.png",  # ploaie
    'snow': "logo/Snow.png",  # zapada
    'snow-thin': "logo/Snow.png",  # lapovita
    'fog': "logo/Haze.png",  # ceata
    'clear-night': "logo/Moon.png",  # cer senin
    'partly-cloudy-night': "logo/PartlyMoon.png",  # nori imprastiati
    'thunderstorm': "logo/Storm.png",  # furtuna
    'tornado': "logo/Tornado.png",    # tornada
    'hail': "logo/Hail.png"  # grindina
}

##### Ceas ######


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initializare timp
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initializare ziua saptamanii
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize data
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p') #hour in 12h format
            else:
                time2 = time.strftime('%H:%M') #hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            self.timeLbl.after(200, self.tick)

####### Vremea ##### 

class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = 'Brasov'
        self.currently = ''
        self.icon = ''
        #grade
        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        #temperatura
        self.locationLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.locationLbl.pack(side=TOP, anchor=W)
        #icon
        self.iconLbl = Label(self.degreeFrm, bg="black")
        self.iconLbl.pack(side=LEFT, anchor=N, padx=20)
        self.currentlyLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.currentlyLbl.pack(side=TOP, anchor=W)
        self.forecastLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.forecastLbl.pack(side=TOP, anchor=W)

        self.get_weather()

    def get_weather(self):
        try:

            if latitude is None and longitude is None:
                # get location
                location_req_url = "http://freegeoip.net/json/%s" % self.get_ip()
                r = requests.get(location_req_url)
                location_obj = json.loads(r.text)

                lat = location_obj[45.38]
                lon = location_obj[24.35]

                location2 = "%s, %s" % ('Brasov', 'RO')

                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, lat,lon,weather_lang,weather_unit)
            else:
                location2 = ""
                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, latitude, longitude, weather_lang, weather_unit)

            r = requests.get(weather_req_url)
            weather_obj = json.loads(r.text)

            degree_sign= u'\N{DEGREE SIGN}'
            temperature2 = "%s%s" % (str(int(weather_obj['currently']['temperature'])), degree_sign)
            currently2 = weather_obj['currently']['summary']
            forecast2 = weather_obj["hourly"]["summary"]
            

            icon_id = weather_obj['currently']['icon']
            icon2 = None

            if icon_id in icon_lookup:
                icon2 = icon_lookup[icon_id]

            if icon2 is not None:
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open(icon2)
                    image = image.resize((100, 100), Image.ANTIALIAS)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)

                    self.iconLbl.config(image=photo)
                    self.iconLbl.image = photo
            else:
                self.iconLbl.config(image='')

            if self.currently != currently2:
                self.currently = currently2
                self.currentlyLbl.config(text=currently2)
            if self.forecast != forecast2:
                self.forecast = forecast2
                self.forecastLbl.config(text=forecast2)
            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)
            if self.location != location2:
                self.location = location2
                self.locationLbl.config(text='Brasov, Romania')
        except Exception as e:
            traceback.print_exc()
            print "Error: %s. Cannot get weather." % e

        self.after(600000, self.get_weather)

    @staticmethod
    def convert_kelvin_to_fahrenheit(kelvin_temp):
        return 1.8 * (kelvin_temp - 273) + 32

##### Stiri ######

class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'News' # 'News' is more internationally generic
        self.newsLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.newsLbl.pack(side=TOP, anchor=W)
        self.headlinesContainer = Frame(self, bg="black")
        self.headlinesContainer.pack(side=TOP)
        self.get_headlines()

    def get_headlines(self):
        try:
            for widget in self.headlinesContainer.winfo_children():
                widget.destroy()
            if news_country_code == None:
                headlines_url = "https://news.google.com/news/rss/?ned=ro&gl=RO&ceid=RO:ro"
            else:
                headlines_url = "https://news.google.com/news/rss/?ned=ro&gl=RO&ceid=RO:ro"
            feed = feedparser.parse(headlines_url)

            for post in feed.entries[0:6]:
                headline = NewsHeadline(self.headlinesContainer, post.title)
                headline.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            print "Error: %s. Cannot get news." % e

        self.after(600000, self.get_headlines)

class NewsHeadline(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')
        image = Image.open("logo/Newspaper.png")
        image = image.resize((25, 25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=N)

        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=RIGHT, anchor=N)

#######Calendar######

class Calendar(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = 'Calendar Events'
        self.calendarLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.calendarLbl.pack(side= TOP, anchor=W)
        self.calendarEventContainer = Frame(self, bg='black')
        self.calendarEventContainer.pack(side=TOP, anchor=W)
        self.get_events()

    def get_events(self):
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 5 events on the user's calendar.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
           with open('token.pickle', 'rb') as token:
             creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
           if creds and creds.expired and creds.refresh_token:
             creds.refresh(Request())
           else:
             flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
             creds = flow.run_local_server()
           # Save the credentials for the next run
           with open('token.pickle', 'wb') as token:
             pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.now().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=5, singleEvents=True,
                                        orderBy='startTime').execute()
        events = events_result.get('items', [])


        for widget in self.calendarEventContainer.winfo_children():
            widget.destroy()

        if not events:
          event_name='No upcoming events found.'
        else:
          for event in events:
           start = event['start'].get('dateTime', event['start'].get('date'))
           dt = dateutil.parser.parse(start)          
           text = event['summary'] + ' ' + str(dt.strftime('%d.%m.%y - %H:%M'))    
           calendar_event = CalendarEvent(self.calendarEventContainer, text)
           calendar_event.pack(side=TOP, anchor=W)
        self.after(10000, self.get_events)

class CalendarEvent(Frame):
    def __init__(self, parent, event_name="Event 1"):
        Frame.__init__(self, parent, bg='black')
        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=TOP, anchor=E)



####### FullScreen ########

class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.attributes("-fullscreen",True)
        self.tk.configure(background='black')
        self.topFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state = True
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)

        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=30, pady=30)

        # weather
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=TOP, anchor=W, padx=30, pady=30)

        # news 
        self.news = News(self.bottomFrame)
        self.news.pack(side=BOTTOM, anchor=W, padx=30, pady=30)
       
        # calender
        self.calender = Calendar(self.bottomFrame)
        self.calender.pack(side = LEFT, anchor=W, padx=50, pady=0)

    def toggle_fullscreen(self, event=None):
        
        self.tk.attributes("fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

if __name__ == '__main__':
    w = FullscreenWindow()
    w.tk.mainloop()