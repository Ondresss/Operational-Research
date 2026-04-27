cmake_minimum_required(VERSION 3.20)
project(VRPGeneticAlg)

set(CMAKE_CXX_STANDARD 26)
find_package(raylib REQUIRED)
find_package(nlohmann_json 3.10 REQUIRED)
find_library(LEMON_LIBRARY NAMES lemon REQUIRED)
find_path(LEMON_INCLUDE_DIR NAMES lemon/list_graph.h REQUIRED)
add_executable(VRPGeneticAlg main.cpp
        VRPGenetic.cpp
        VRPGenetic.h
        Depot.cpp
        Depot.h
        Customer.cpp
        Customer.h
)
include_directories(/usr/local/include ${LEMON_INCLUDE_DIR})
link_directories(/usr/local/lib)
target_compile_options(VRPGeneticAlg PRIVATE -fsanitize=address -fsanitize=undefined)
target_link_options(VRPGeneticAlg PRIVATE -fsanitize=address -fsanitize=undefined)
target_link_libraries(VRPGeneticAlg PRIVATE raylib
        nlohmann_json::nlohmann_json
        ${LEMON_LIBRARY})