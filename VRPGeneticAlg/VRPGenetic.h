//
// Created by andrew on 4/21/26.
//

#pragma once
#include <string>
#include <lemon/list_graph.h>
#include <fstream>
#include <nlohmann/json.hpp>
#include "Customer.h"
class VRPGenetic {
public:
    struct Individual {
        std::vector<std::vector<lemon::ListGraph::Edge>> routes;
        double fitness = 0.0;;
    };
    enum NodeType { DEPOT = 0, CUSTOMER = 1 };
    VRPGenetic(const std::string& filename);


    double earthDistance(const lemon::ListGraph::Node& n1,const lemon::ListGraph::Node& n2 );
private:
    std::size_t vehicleCount = 0;
    std::size_t vehicleCapacity = 0;
    int vehicleSpeed = 0;

    std::vector<lemon::ListGraph::Node> nodes;
    std::vector<Customer> customers;
    std::vector<Depot> depots;
    lemon::ListGraph graph;

    lemon::ListGraph::NodeMap<int> typeMap;
    lemon::ListGraph::NodeMap<int> demandMap;
    lemon::ListGraph::NodeMap<double> latMap;
    lemon::ListGraph::NodeMap<double> lonMap;
    lemon::ListGraph::NodeMap<int> startTimeMap;
    lemon::ListGraph::NodeMap<int> endTimeMap;
    lemon::ListGraph::NodeMap<int> serviceTimeMap;

    lemon::ListGraph::EdgeMap<double> distanceMap;
    lemon::ListGraph::EdgeMap<double> travelTimeMap;

    void load(const std::string& filename);
    void fillNodes();
    void fillEdges();

};

