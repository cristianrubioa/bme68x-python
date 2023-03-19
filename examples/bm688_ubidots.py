import requests
import time
import bme680
from smbus import SMBus

# Ubidots
TOKEN = ""
DEVICE_LABEL = "bm688"  
BASE_URL = "http://industrial.api.ubidots.com/api/v1.6/devices/"

# I2C
I2C_ADDR = 0x77
BUS = SMBus(5)


class BME688(bme680.BME680):
    def __init__(self, i2c_addr=I2C_ADDR, i2c_bus=BUS) -> None:
        super().__init__(i2c_addr, i2c_bus)
        self.calibration()

        # oversampling settings
        self.set_humidity_oversample(bme680.OS_2X)
        self.set_pressure_oversample(bme680.OS_4X)
        self.set_temperature_oversample(bme680.OS_8X)
        self.set_filter(bme680.FILTER_SIZE_3)
        self.set_gas_status(bme680.ENABLE_GAS_MEAS)
        
        self.initial_reading()
        self.set_gas_heater_temperature(320)
        self.set_gas_heater_duration(150)
        self.select_gas_heater_profile(0)


    def calibration(self) -> None:
        print("Calibration data:")
        calibration_data = self.calibration_data
        for name in dir(calibration_data):
            if not name.startswith("_"):
                value = getattr(calibration_data, name)

                if isinstance(value, int):
                    print(f"{name}: {value}")


    def initial_reading(self) -> None:
        print("\n\nInitial reading:")
        sensor_data = self.data
        for name in dir(sensor_data):
            value = getattr(sensor_data, name)

            if not name.startswith("_"):
                print(f"{name}: {value}")

    def build_payload(self):
        sensor_data = self.data
        payload = {
            "temperature": sensor_data.temperature,
            "pressure": sensor_data.pressure,
            "humidity": sensor_data.humidity,
        }
        if sensor_data.heat_stable:
            payload["gas_resistance"] = sensor_data.gas_resistance

        return payload 


def send_ubidots(payload):
    # Make the HTTP request to Ubidots
    url = f"{BASE_URL}{DEVICE_LABEL}/?token={TOKEN}"
    status = 400
    attempts = 0

    while status >= 400 and attempts <= 5:
        req = requests.post(url, json=payload)
        status = req.status_code
        attempts += 1

    response = req.json()

    return response
    

if __name__ == "__main__":
    bme688 = BME688()
    print("\n\nPolling:")

    try:
        while True:
            if bme688.get_sensor_data():
                payload = bme688.build_payload()
                response = send_ubidots(payload)
                print(f"response json from server: \n{response}")

            time.sleep(1)

    except KeyboardInterrupt:
        pass
