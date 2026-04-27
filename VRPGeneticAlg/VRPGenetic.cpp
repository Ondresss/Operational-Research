//
// Created by andrew on 4/21/26.
//

#include "VRPGenetic.h"

VRPGenetic::VRPGenetic(const std::string& filename) :
      vehicleCapacity(0),
      vehicleCount(0),
      graph(),
      typeMap(graph),
      demandMap(graph),
      latMap(graph),
      lonMap(graph),
      startTimeMap(graph),
      endTimeMap(graph),
      serviceTimeMap(graph),
      distanceMap(graph),
      travelTimeMap(graph){
        this->load(filename);
        this->fillNodes();
        this->fillEdges();
}
void VRPGenetic::load(const std::string& filename) {
    std::ifstream inFile(filename);
    if (!inFile.is_open()) {
        throw std::runtime_error("Could not open file: " + filename);
    }

    nlohmann::json data = nlohmann::json::parse(inFile);

    this->vehicleCount = data["vehicles"]["count"];
    this->vehicleCapacity = data["vehicles"]["capacity"];
    this->vehicleSpeed = data["vehicles"]["speed"];
    for (const auto& d : data["depots"]) {
        depots.emplace_back(
            d["id"].get<std::string>(),
            d["address"].get<std::string>(),
            d["lat"].get<double>(),
            d["lon"].get<double>(),
            d["time_window"][0].get<int>(),
            d["time_window"][1].get<int>(),
            d["service"].get<int>()
        );
    }

    for (const auto& c : data["customers"]) {
        customers.emplace_back(
            c["id"].get<std::string>(),
            c["lat"].get<double>(),
            c["lon"].get<double>(),
            c["demand"].get<int>(),
            c["time_window"][0].get<int>(),
            c["time_window"][1].get<int>(),
            c["service"].get<int>()
        );
    }

    std::cout << "Loaded: " << depots.size() << " dep a "
              << customers.size() << " customers." << std::endl;
}


double VRPGenetic::earthDistance(const lemon::ListGraph::Node& n1,const lemon::ListGraph::Node& n2 ) {
    double lat1 = this->latMap[n1];
    double lat2 = this->latMap[n2];
    double lon1 = this->lonMap[n1];
    double lon2 = this->lonMap[n2];

    const double R = 6371.0;
    double dLat = (lat2 - lat1) * M_PI / 180.0;
    double dLon = (lon2 - lon1) * M_PI / 180.0;

    double a = std::sin(dLat / 2) * std::sin(dLat / 2) +
               std::cos(lat1 * M_PI / 180.0) * std::cos(lat2 * M_PI / 180.0) *
               std::sin(dLon / 2) * std::sin(dLon / 2);

    double c = 2 * std::atan2(std::sqrt(a), std::sqrt(1 - a));
    return R * c;
}


void VRPGenetic::fillNodes() {
    for (auto& d : depots) {
        lemon::ListGraph::Node n = this->graph.addNode();
        this->nodes.push_back(n);
        Location loc = d.getLocation();
        this->typeMap[n] = NodeType::DEPOT;
        this->latMap[n] = loc.latitude;
        this->lonMap[n] = loc.longitude;
        this->demandMap[n] = d.getDemand();
    }

    for (auto& c : customers) {
        lemon::ListGraph::Node n = this->graph.addNode();
        this->nodes.push_back(n);
        Location loc = c.getLocation();
        this->typeMap[n] = NodeType::CUSTOMER;
        this->latMap[n] = loc.latitude;
        this->lonMap[n] = loc.longitude;
        this->demandMap[n] = c.getDemand();
    }

}

void VRPGenetic::fillEdges() {
    for (size_t i = 0; i < nodes.size(); ++i) {
        for (size_t j = i + 1; j < nodes.size(); ++j) {
            lemon::ListGraph::Edge e = graph.addEdge(nodes[i], nodes[j]);
            const double dist = this->earthDistance(
                this->nodes[i],
                this->nodes[j]
            );
            distanceMap[e] = dist;
            if (this->vehicleSpeed > 0) {
                travelTimeMap[e] = (dist / static_cast<double>(this->vehicleSpeed)) * 60.0;
            } else {
                travelTimeMap[e] = 0.0;
            }
        }
    }
}