#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <algorithm>
#include <numeric>

// Moving average
std::vector<double> moving_average(const std::vector<double>& prices, int window) {
    std::vector<double> result;
    if (prices.size() < window || window <= 0) return result;
    double sum = std::accumulate(prices.begin(), prices.begin() + window, 0.0);
    result.push_back(sum / window);
    for (size_t i = window; i < prices.size(); ++i) {
        sum += prices[i] - prices[i - window];
        result.push_back(sum / window);
    }
    return result;
}

// Min value
double min_price(const std::vector<double>& prices) {
    if (prices.empty()) return 0.0;
    return *std::min_element(prices.begin(), prices.end());
}

// Max value
double max_price(const std::vector<double>& prices) {
    if (prices.empty()) return 0.0;
    return *std::max_element(prices.begin(), prices.end());
}

// Sum
double sum_prices(const std::vector<double>& prices) {
    return std::accumulate(prices.begin(), prices.end(), 0.0);
}

PYBIND11_MODULE(fast_market, m) {
    m.def("moving_average", &moving_average, "Compute moving average", pybind11::arg("prices"), pybind11::arg("window"));
    m.def("min_price", &min_price, "Get min price", pybind11::arg("prices"));
    m.def("max_price", &max_price, "Get max price", pybind11::arg("prices"));
    m.def("sum_prices", &sum_prices, "Sum prices", pybind11::arg("prices"));
} 