#include <pybind11/pybind11.h>
#include <string>

namespace py = pybind11;

const std::string KEY1 = "DB_KEY_ALPHA_2025";
const std::string KEY2 = "DB_KEY_BRAVO_9981";

std::string crypt(std::string data, std::string key) {
    std::string out = data;
    for (size_t i = 0; i < data.size(); ++i) out[i] = data[i] ^ key[i % key.size()];
    return out;
}

std::string enc1(std::string s) { return crypt(s, KEY1); }
std::string enc2(std::string s) { return crypt(s, KEY2); }
std::string dec1(std::string s) { return crypt(s, KEY1); }
std::string dec2(std::string s) { return crypt(s, KEY2); }

PYBIND11_MODULE(secure_codex, m) {
    m.def("encoder1", &enc1); m.def("decoder1", &dec1);
    m.def("encoder2", &enc2); m.def("decoder2", &dec2);
}
