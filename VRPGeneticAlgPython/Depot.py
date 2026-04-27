from Location import  Location

class Depot(Location):
    def __init__(self, id, lat, lon, service_time, time_window,demand):
        super().__init__(id, lat, lon, service_time, time_window)
        self.type = "DEPOT"
        self.demand = demand