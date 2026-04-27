//
// Created by andrew on 4/21/26.
//

#pragma once
#include <cstddef>
#include <string>
#include <vector>
#include <iostream>
struct TimeWindow {
    int start;
    int end;
};

struct Location {
    double longitude = 0.0;
    double latitude = 0.0;
};

class Depot {
public:
    Depot(std::string id, std::string name, double lat, double lon,
          int tw_start, int tw_end, int serviceTime = 0)
        : id(std::move(id)), name(std::move(name)), demand(0), service(serviceTime)
    {
        loc.latitude = lat;
        loc.longitude = lon;
        timeWindow.start = tw_start;
        timeWindow.end = tw_end;
    }

    [[nodiscard]] std::string getId() const { return id; }
    [[nodiscard]] Location getLocation() const { return loc; }
    [[nodiscard]] TimeWindow getTimeWindow() const { return timeWindow; }
    [[nodiscard]] int getDemand() const { return demand; }
    void printInfo() const {
        std::cout << "Depot: " << name << " [" << id << "]\n"
                  << "  GPS: " << loc.latitude << ", " << loc.longitude << "\n"
                  << "  Okno: " << timeWindow.start << "-" << timeWindow.end << " min\n";
    }

private:
    std::string id;
    std::string name;
    Location loc;
    int demand = 0;
    TimeWindow timeWindow{};
    int service = 0;
};