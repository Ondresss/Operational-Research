class Location:
    def __init__(self, id, lat, lon, service_time, time_window):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.service_time = service_time
        self.start_time = time_window[0]
        self.end_time = time_window[1]