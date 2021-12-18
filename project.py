# import sys
from flask import Flask, render_template, request
import json, urllib, requests, calendar, datetime, logging
from keys import weather_key, pxl_key

# sys.path.append('/users/shi ming/appdata/local/programs/python/python39/lib/site-packages')
# from requests_oauthlib import OAuth1

app = Flask(__name__)


# the safe_get function from class to make API calls
def safe_get(url):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print("The server couldn't fulfill the request.\nDouble check search query.")
        print("Error code:", e.code)
    except urllib.error.URLError as e:
        print("Failed to reach server")
        print("Reason:", e.reason)
    return None


# Takes in a city as string and returns the coordinates of that city as a tuple: (lat, lon)
def get_coordinates(city):
    base_url = "https://api.openweathermap.org/data/2.5/weather?"
    params = {"appid": weather_key, "q": city}
    paramstr = urllib.parse.urlencode(params)
    req_weather_data = safe_get(base_url + paramstr)
    if req_weather_data is None:
        return None
    else:
        weather_data = json.load(req_weather_data)
        # print(weather_data)
        return weather_data["coord"]["lat"], weather_data["coord"]["lon"]


# Takes in the coordinates and preferred units (for temperatures) of a location
# Returns a json containing the weather data for that location
def get_weather_data(coordinates, units):
    baseurl = "https://api.openweathermap.org/data/2.5/onecall?"
    params = {
        "appid": weather_key, "lat": coordinates[0], "lon": coordinates[1],
        "units": units, "exclude": "minutely,hourly", "lang": "en"
    }
    paramstr = urllib.parse.urlencode(params)
    req = safe_get(baseurl + paramstr)
    return json.load(req)


# def current_timestamp():
#     date = datetime.datetime.utcnow()
#     utc_time = calendar.timegm(date.utctimetuple())
#     return utc_time

# Takes in a unix timestamp and returns its corresponding date formatted: MM-DD-YYYY
def convert_time(dt):
    date_time = datetime.datetime.fromtimestamp(dt)
    return date_time.strftime('%m/%d/%y')


# Takes in a unix timestamp and returns the day of the week
def convert_day(dt):
    return datetime.datetime.fromtimestamp(dt).strftime("%A")


# Takes in the coordinates of city and the time of the past forecast data UTC
def get_past_weather_data(coordinates, units, dt):  # 1 day = 86400 seconds unix timestamp
    baseurl = "http://api.openweathermap.org/data/2.5/onecall/timemachine?"
    params = {"appid": weather_key, "lat": coordinates[0], "lon": coordinates[1], "dt": dt, "units": units,
              "lang": "en", "exclude": "hourly,minutely,daily"}
    paramstr = urllib.parse.urlencode(params)
    req_past_data = safe_get(baseurl + paramstr)
    return json.load(req_past_data)


# Takes in weather icon as a string and returns the png url of the icon
def get_weather_icon(icon):
    url = "http://openweathermap.org/img/wn/%s@2x.png"
    return url % icon


# Takes in the city name and returns a json containing an image of the city from Pexel
def get_city_img(city):
    url = "https://api.pexels.com/v1/search?query=%s&per_page=1" % city
    header = {"Authorization": pxl_key}
    try:
        return requests.get(url, headers=header).json()
    except requests.exceptions.RequestException as e:
        print("Request cannot be fulfilled")
        print(e)
    return None


# Takes in a string of words and return a capitalized/formatted version of the words as a string
def format_words(words):
    words = words.split()
    for word in range(len(words)):
        capitalized = words[word][0].upper() + words[word][1:].lower()
        words[word] = capitalized
    return " ".join(words)


# Takes in forecast data and returns the average temperature in degrees F and C, respectively
def take_forecast_avg(data):
    total_f = 0.0
    total_c = 0.0
    for day in range(7):
        total_c += data[day]["cel"]["day"]
        total_f += data[day]["temp"]["day"]
    print()
    return round(total_f / 7, 2), round(total_c / 7, 2)


# Takes in past weather data and returns the average temperature in degrees F and C, respectively
def take_past_avg(data):
    total_f = 0.0
    total_c = 0.0
    for day in data:
        total_c += day["cel"]
        total_f += day["temp"]
    print()
    return round(total_f / 5, 2), round(total_c / 5, 2)


@app.route("/", methods=["GET", "POST"])
def main_route():
    app.logger.info("In main route")
    if request.method == "POST":
        app.logger.info(request.form.get("place"))
        name = request.form.get("place")
        if get_coordinates(name) is not None:
            location = get_coordinates(name)
            data = get_weather_data(location, "imperial")
            altdata = get_weather_data(location, "metric")
            data['current']['cel'] = get_weather_data(location, "metric")['current']['temp']
            curr_time = data['current']['dt']
            data['current']['date'] = convert_time(curr_time)
            data['current']['day'] = convert_day(curr_time)
            print(data['current']['day'])
            past_data = []
            for day in range(5, 0, -1):
                day_data = get_past_weather_data(location, "imperial", curr_time - (day * 86400))['current']
                day_data['date'] = convert_time(day_data['dt'])
                day_data['day'] = convert_day(day_data['dt'])
                day_data['cel'] = get_past_weather_data(
                    location, "metric", curr_time - (day * 86400))['current']['temp']
                past_data.append(day_data)
            print(past_data[0])
            print()
            print(len(data['current']))
            print(data['current'])
            print()
            del data['daily'][0]
            for day in data['daily']:
                day['date'] = convert_time(day['dt'])
                day['day'] = convert_day(day['dt'])
            del altdata['daily'][0]
            for day in range(len(altdata['daily'])):
                data['daily'][day]['cel'] = altdata['daily'][day]['temp']
            img_dt = get_city_img(name)
            forecast_avg = take_forecast_avg(data["daily"])
            past_avg = take_past_avg(past_data)
            analytics = {
                "forecast_avg": forecast_avg,
                "past_avg": past_avg
            }

            title = "Weather for %s" % format_words(name)
            if (data is not None) & (img_dt is not None):
                return render_template("index.html", page_title=title, current_data=data['current'],
                                       forecast=data['daily'], past_data=past_data, img=img_dt, more=analytics)
            elif data is not None:
                return render_template("index.html", page_title=title, current_data=data['current'],
                                       forecast=data['daily'], past_data=past_data, more=analytics)
            else:
                return render_template("index.html", page_title="Simple Weather - Error",
                                       prompt="Oh no! API call was unsuccessful")
        else:
            return render_template("index.html", page_title="home",
                                   prompt="City name invalid! Please try again.")
    else:
        return render_template("index.html", page_title="Home")


@app.route("/analysis")
def input_route():
    pass


def main():
    coordinates = get_coordinates("seaTTLe")
    print(coordinates[0], coordinates[1])
    data = get_weather_data(coordinates, "imperial")
    print(data.keys())
    print(data)
    # print(len((data["daily"][0])))
    # print(get_weather_icon(data["current"]["weather"][0]["icon"]))
    print(format_words("LOS angeLES"))
    print(format_words("seaTTLe"))
    print(format_words("chiCaGo"))
    print(format_words("new YORK"))
    print(format_words("salT LaKe City"))
    slt = get_coordinates("salT LaKe City")
    print(slt)


if __name__ == "__main__":
    # main()
    app.run(host="localhost", port=8080, debug=True)
