import json
import folium
import os
from os.path import join, dirname
from dotenv import load_dotenv
import requests
from geopy.distance import distance
from flask import Flask


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = \
        response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_house_dist(house):
    return house["distance"]


def draw_map(user_place, user_coords, nearest_houses):
    coffee_map = folium.Map(location=list(user_coords))
    tooltip = "Check me!"
    for coffee_house in nearest_houses:
        folium.Marker([coffee_house["latitude"], coffee_house["longitude"]],
                      popup=f"<i>{coffee_house['title']}</i>",
                      tooltip=tooltip).add_to(coffee_map)
    coffee_map.save(join("sources", "coffee_map.html"))


def return_map():
    with open(join("sources", "coffee_map.html")) as map:
        return map.read()


def main():

    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    apikey = os.getenv("GEODATA_KEY")

    with open("coffee.json", "r", encoding="CP1251") as file:
        coffee_houses_json = file.read()

    coffee_houses = json.loads(coffee_houses_json)
    user_place = input("Where are you? ")
    user_coords = fetch_coordinates(apikey, user_place)
    user_coords = user_coords[::-1]  # replace longitude and latitude for
    usefull_information = []         # fetch_coordinates()

    for coffee_house in coffee_houses:
        one_house_information = {}
        one_house_information["title"] = coffee_house["Name"]
        house_coords = coffee_house["geoData"]["coordinates"][1], \
            coffee_house["geoData"]["coordinates"][0]
        dist_to_house = distance(user_coords, house_coords).km
        one_house_information["distance"] = dist_to_house
        one_house_information["latitude"] = house_coords[0]
        one_house_information["longitude"] = house_coords[1]
        usefull_information.append(one_house_information)

    nearest_houses = sorted(usefull_information, key=get_house_dist)[:5]
    draw_map(user_place, user_coords, nearest_houses)
    app = Flask(__name__)
    app.add_url_rule("/", "coffee_map", return_map)
    app.run()


if __name__ == "__main__":
    main()
