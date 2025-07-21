cmake_minimum_required(VERSION 3.16)
project(TradingBot VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set build type to Release if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS "-Wall -Wextra")
set(CMAKE_CXX_FLAGS_DEBUG "-g")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")

# Find required packages
find_package(Boost REQUIRED COMPONENTS system filesystem thread)
find_package(benchmark REQUIRED)

# SQLite - try pkg-config first, then fallback to find_package
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(SQLite3 REQUIRED sqlite3)
else()
    find_package(SQLite3 REQUIRED)
    # Create imported target for compatibility
    if(NOT TARGET SQLite3::SQLite3)
        add_library(SQLite3::SQLite3 UNKNOWN IMPORTED)
        set_target_properties(SQLite3::SQLite3 PROPERTIES
            IMPORTED_LOCATION "${SQLite3_LIBRARIES}"
            INTERFACE_INCLUDE_DIRECTORIES "${SQLite3_INCLUDE_DIRS}")
    endif()
endif()

# OpenSSL for secure connections
find_package(OpenSSL REQUIRED)

# nlohmann/json for JSON parsing
find_package(nlohmann_json REQUIRED)

# cURL for HTTP requests
find_package(CURL REQUIRED)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/src)
include_directories(${CMAKE_SOURCE_DIR}/include)

# Source files
set(SOURCES
    src/main.cpp
    src/engine/trading_engine.cpp
    src/data/websocket_client.cpp
    src/data/market_data.cpp
    src/strategy/strategy_interface.cpp
    src/strategy/momentum_strategy.cpp
    src/strategy/mean_reversion_strategy.cpp
    src/risk/risk_manager.cpp
    src/execution/order_executor.cpp
    src/database/database_manager.cpp
    src/web/web_server.cpp
    src/benchmark/latency_profiler.cpp
    src/backtest/backtest_engine.cpp
    src/utils/logger.cpp
    src/utils/config.cpp
    src/exchange/binance_client.cpp
)

# Header files
set(HEADERS
    include/engine/trading_engine.h
    include/data/websocket_client.h
    include/data/market_data.h
    include/strategy/strategy_interface.h
    include/strategy/momentum_strategy.h
    include/strategy/mean_reversion_strategy.h
    include/risk/risk_manager.h
    include/execution/order_executor.h
    include/database/database_manager.h
    include/web/web_server.h
    include/benchmark/latency_profiler.h
    include/backtest/backtest_engine.h
    include/utils/logger.h
    include/utils/config.h
    include/exchange/binance_client.h
)

# Create executable
add_executable(trading_bot ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(trading_bot
    Boost::system
    Boost::filesystem
    Boost::thread
    OpenSSL::SSL
    OpenSSL::Crypto
    nlohmann_json::nlohmann_json
    benchmark::benchmark
    CURL::libcurl
    pthread
)

# Link SQLite3 - handle both pkg-config and find_package cases
if(PkgConfig_FOUND AND SQLite3_FOUND)
    target_link_libraries(trading_bot ${SQLite3_LIBRARIES})
    target_include_directories(trading_bot PRIVATE ${SQLite3_INCLUDE_DIRS})
else()
    target_link_libraries(trading_bot SQLite3::SQLite3)
endif()

# Simple WebSocket test
add_executable(simple_websocket
    simple_websocket.cpp
)

target_link_libraries(simple_websocket
    Boost::system
    Boost::filesystem
    Boost::thread
    OpenSSL::SSL
    OpenSSL::Crypto
    nlohmann_json::nlohmann_json
)

# Debug test executable
add_executable(debug_test
    debug_test.cpp
    src/utils/logger.cpp
    src/utils/config.cpp
    src/benchmark/latency_profiler.cpp
    src/data/market_data.cpp
)

target_link_libraries(debug_test
    Boost::system
    Boost::filesystem
    Boost::thread
    OpenSSL::SSL
    OpenSSL::Crypto
    nlohmann_json::nlohmann_json
    benchmark::benchmark
    pthread
)

# Link SQLite3 for debug test
if(PkgConfig_FOUND AND SQLite3_FOUND)
    target_link_libraries(debug_test ${SQLite3_LIBRARIES})
    target_include_directories(debug_test PRIVATE ${SQLite3_INCLUDE_DIRS})
else()
    target_link_libraries(debug_test SQLite3::SQLite3)
endif()

# Minimal bot executable (for testing without database issues)
add_executable(minimal_bot
    minimal_bot.cpp
    src/web/web_server.cpp
    src/utils/logger.cpp
    src/utils/config.cpp
    src/engine/trading_engine.cpp
    src/strategy/strategy_interface.cpp
    src/strategy/momentum_strategy.cpp
    src/strategy/mean_reversion_strategy.cpp
    src/database/database_manager.cpp
    src/risk/risk_manager.cpp
    src/execution/order_executor.cpp
    src/benchmark/latency_profiler.cpp
    src/backtest/backtest_engine.cpp
    src/exchange/binance_client.cpp
)

target_link_libraries(minimal_bot
    Boost::system
    Boost::filesystem
    Boost::thread
    OpenSSL::SSL
    OpenSSL::Crypto
    nlohmann_json::nlohmann_json
    benchmark::benchmark
    CURL::libcurl
    pthread
)

# Link SQLite3 for minimal_bot
if(PkgConfig_FOUND AND SQLite3_FOUND)
    target_link_libraries(minimal_bot ${SQLite3_LIBRARIES})
    target_include_directories(minimal_bot PRIVATE ${SQLite3_INCLUDE_DIRS})
else()
    target_link_libraries(minimal_bot SQLite3::SQLite3)
endif()

# Separate backtest executable
add_executable(backtest_runner
    src/backtest/backtest_main.cpp
    src/backtest/backtest_engine.cpp
    src/strategy/strategy_interface.cpp
    src/strategy/momentum_strategy.cpp
    src/strategy/mean_reversion_strategy.cpp
    src/database/database_manager.cpp
    src/utils/logger.cpp
    src/utils/config.cpp
)

target_link_libraries(backtest_runner
    Boost::system
    Boost::filesystem
    Boost::thread
    nlohmann_json::nlohmann_json
    pthread
)

# Link SQLite3 for backtest runner
if(PkgConfig_FOUND AND SQLite3_FOUND)
    target_link_libraries(backtest_runner ${SQLite3_LIBRARIES})
    target_include_directories(backtest_runner PRIVATE ${SQLite3_INCLUDE_DIRS})
else()
    target_link_libraries(backtest_runner SQLite3::SQLite3)
endif()

# Binance Testnet test
add_executable(binance_test
    binance_test.cpp
    src/exchange/binance_client.cpp
    src/utils/logger.cpp
    src/utils/config.cpp
)

target_link_libraries(binance_test
    Boost::system
    Boost::filesystem
    Boost::thread
    OpenSSL::SSL
    OpenSSL::Crypto
    nlohmann_json::nlohmann_json
    CURL::libcurl
    pthread
)

# Installation
install(TARGETS trading_bot backtest_runner binance_test
    DESTINATION bin
)

# Copy configuration files
install(FILES config/config.json
    DESTINATION etc/trading_bot
)

# Copy web assets
install(DIRECTORY web/static
    DESTINATION share/trading_bot/web
) 