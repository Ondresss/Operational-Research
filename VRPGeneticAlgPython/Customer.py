from Location import Location

class Customer(Location):
    def __init__(self, id, lat, lon, service_time, time_window, demand):
        super().__init__(id, lat, lon, service_time, time_window)
        self.demand = demand
        self.type = "CUSTOMER"