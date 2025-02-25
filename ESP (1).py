# UNI 137 - Sophos

import network
import time
import dht
import urequests
import ujson
from umqtt.simple import MQTTClient
from machine import Pin

# ====== KONFIGURASI WIFI ======
SSID = "The villalt1"  
PASSWORD = "Gudangroti"  

# ====== KONFIGURASI UBIDOTS STEM ======
UBIDOTS_TOKEN = "BBUS-uuLFJmVsjAVfp91HsPMZsPGzDD3hfG"  
MQTT_BROKER  = "industrial.api.ubidots.com"
MQTT_CLIENT_ID = "esp32_dht11"
DEVICE_LABEL = "esp32"
VARIABLE_TEMP = "temperature"
VARIABLE_HUM = "humidity"
VARIABLE_MOTION = "motion"
MQTT_TOPIC = f"/v1.6/devices/{DEVICE_LABEL}"

# ====== KONFIGURASI API FLASK (MONGODB) ======
API_URL = "http://192.168.1.105:5000/dht11"  

# ====== FUNGSI KONEKSI WIFI ======
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        print("Menghubungkan ke WiFi...")
        time.sleep(1)

    print("Terhubung ke WiFi:", wlan.ifconfig())

# ====== FUNGSI KONEKSI MQTT UBIDOTS ======
def connect_mqtt():
    try:
        client = MQTTClient(
            MQTT_CLIENT_ID,
            MQTT_BROKER,
            port=1883,
            user=UBIDOTS_TOKEN,
            password="",  
        )
        client.connect()
        print("Terhubung ke MQTT Ubidots!")
        return client
    except Exception as e:
        print("Gagal terhubung ke MQTT:", e)
        return None

# ====== INISIALISASI SENSOR DHT11 & PIR ======
dht_pin = Pin(2)  # Sensor DHT11 pada D2 di ESP32
sensor_dht = dht.DHT11(dht_pin)

pir_pin = Pin(5, Pin.IN)  # Sensor PIR pada D5 di ESP32

led = Pin(21, Pin.OUT) # LED pada D21 di ESP32
# Hubungkan WiFi
connect_wifi()

# Loop utama
while True:
    # Pastikan MQTT tetap terhubung
    mqtt_client = connect_mqtt()
    if mqtt_client is None:
        print("Mencoba ulang koneksi ke MQTT...")
        time.sleep(5)
        continue  

    try:
        # Baca data dari DHT11
        sensor_dht.measure()
        suhu = sensor_dht.temperature()
        kelembaban = sensor_dht.humidity()

        # Baca data dari sensor PIR
        motion_status = pir_pin.value()  # 1 = Gerakan terdeteksi, 0 = Tidak ada gerakan
        
        # led nyala kalau ada gerakan
        led.value(motion_status)

        # Format data JSON
        data = ujson.dumps({
            VARIABLE_TEMP: suhu,
            VARIABLE_HUM: kelembaban,
            VARIABLE_MOTION: motion_status
        })

        print("Mengirim data ke Ubidots:", data)
        mqtt_client.publish(MQTT_TOPIC, data)  

        # Kirim data ke API Flask (MongoDB)
        try:
            response = urequests.post(API_URL, json={
                "temperature": suhu,
                "humidity": kelembaban,
                "motion": motion_status
            })
            print("Data berhasil dikirim ke API Flask:", response.text)
            response.close()
        except Exception as e:
            print("Gagal mengirim ke API Flask:", e)

    except OSError as e:
        print("Gagal membaca sensor:", e)

    time.sleep(5)  # Kirim setiap 5 detik