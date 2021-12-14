# import sys
from flask import Flask, render_template, request
import json, urllib, requests, calendar, datetime, logging
from keys import weather_key, pxl_key

# sys.path.append('/users/shi ming/appdata/local/programs/python/python39/lib/site-packages')
# from requests_oauthlib import OAuth1

app = Flask(__name__)


# the safe_get function from class
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
    print(base_url + paramstr)
    weather_data = json.load(req_weather_data)
    # print(weather_data)
    return weather_data["coord"]["lat"], weather_data["coord"]["lon"]


def get_weather_data(coordinates):
    baseurl = "https://api.openweathermap.org/data/2.5/onecall?"
    params = {
        "appid": weather_key, "lat": coordinates[0], "lon": coordinates[1],
        "units": "metric", "exclude": "minutely,hourly", "lang": "en"
    }
    paramstr = urllib.parse.urlencode(params)
    req = safe_get(baseurl + paramstr)
    return json.load(req)


# def current_timestamp():
#     date = datetime.datetime.utcnow()
#     utc_time = calendar.timegm(date.utctimetuple())
#     return utc_time


# Takes in the coordinates of city and the time of the past forecast data UTC
def get_past_weather_data(coordinates, dt):  # 1 day = 86400 seconds unix timestamp
    baseurl = "http://api.openweathermap.org/data/2.5/onecall/timemachine?"
    params = {"appid": weather_key, "lat": coordinates[0], "lon": coordinates[1], "dt": dt, "units": "metric",
              "lang": "en", "exclude": "hourly,minutely,daily"}
    paramstr = urllib.parse.urlencode(params)
    req_past_data = safe_get(baseurl + paramstr)
    return json.load(req_past_data)


# Takes in weather icon as a string and returns the png url of the icon
def get_weather_icon(icon):
    url = "http://openweathermap.org/img/wn/%s@2x.png"
    return url % icon


@app.route("/", methods=["GET", "POST"])
def main_route():
    app.logger.info("In main route")
    if request.method == "POST":
        app.logger.info(request.form.get("place"))
        name = request.form.get("place")
        # app.logger.info(name)
        if name:
            print("Processing the user's input")
            location = get_coordinates(name)
            data = get_weather_data(location)
            # print(current_timestamp())  # prints current unix timestamp
            # print(data.keys())  # keys: lat,lon,timezone,timezone-offset, current, daily
            print(data['current']['dt'])
            curr_time = data['current']['dt']
            past_data = []
            for day in range(5, 0, -1):
                past_data.append(get_past_weather_data(location, curr_time - (day * 86400))['current'])
            print(past_data)
            print()
            print(len(data['current']))
            print(data['current'])
            print()
            print(data['daily'])
            del data['daily'][0]
            if data is not None:
                title = "Weather data for %s" % name
                return render_template("index.html", page_title=title, current_data=data['current'],
                                       forecast=data['daily'], past_data=past_data)
            else:
                return render_template("index.html", page_title="Simple Weather - Error",
                                       prompt="Oh no! API call was unsuccessful")
        else:
            return render_template("index.html", page_title="home",
                                   prompt="Please enter the city you wish to see the weather")
    else:
        return render_template("index.html", page_title="Home")


@app.route("/userinput")
def input_route():
    pass


def main():
    print("-----")
    coordinates = get_coordinates("seaTTLe")
    print(coordinates[0], coordinates[1])
    data = get_weather_data(coordinates)
    print(data.keys())
    print(data)
    # print(len((data["daily"][0])))
    # print(get_weather_icon(data["current"]["weather"][0]["icon"]))

    # print()
    # get_past_weather_data()


if __name__ == "__main__":
    # main()
    app.run(host="localhost", port=8080, debug=True)
