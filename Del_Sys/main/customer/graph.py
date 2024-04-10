
import math

def calculate_distance(lat1, lng1, lat2, lng2):
    # Convert latitude and longitude from degrees to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

    # Calculate the differences between the latitudes and longitudes
    dlat = lat2 - lat1
    dlon = lng2 - lng1

    # Calculate the Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance in kilometers
    distance = 6371 * c

    # Calculate the duration based on the distance and a speed of 20 km/h
    duration = distance / 20

    # Calculate the price based on the distance and a price of 80 rs/km
    price = distance * 80

    return distance, duration, price