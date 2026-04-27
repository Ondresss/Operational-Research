//
// Created by andrew on 4/21/26.
//
#pragma once
#include <string>
#include  "Depot.h"
class Customer {
public:
    Customer(std::string id, double lat, double lon, int demand,
             int tw_start, int tw_end, int service)
        : id(std::move(id)), demand(demand), service(service) {
        loc.latitude = lat;
        loc.longitude = lon;
        timeWindow.start = tw_start;
        timeWindow.end = tw_end;
    }
    [[nodiscard]] std::string getId() const { return id; }
    [[nodiscard]] Location getLocation() const { return loc; }
    [[nodiscard]] TimeWindow getTimeWindow() const { return timeWindow; }
    [[nodiscard]] int getDemand() const { return demand; }
private:
    std::string id;
    Location loc;
    int demand;
    TimeWindow timeWindow{};
    int service;
};