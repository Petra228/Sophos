from flask import Flask, request, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
import socket
from datetime import datetime
import threading

# ====== KONEKSI KE MONGODB ======
uri = "mongodb+srv://bintangananda405:q7fDFSL6V0eIjCm4@cluster-bintang.1o763.mongodb.net/?retryWrites=true&w=majority&appName=Cluster-Bintang"
client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("✅ Berhasil terhubung ke MongoDB!")
except Exception as e:
    print("❌ Gagal terhubung ke MongoDB:", e)

# ====== KONFIGURASI DATABASE ======
db = client['myDB']
collection = db['sensorData']

# ====== DAPATKAN IP LOKAL ======
local_ip = socket.gethostbyname(socket.gethostname())
print(f"🌍 IP Lokal: {local_ip}")

# ====== INISIALISASI FLASK ======
app = Flask(__name__)

@app.route("/dht11", methods=["POST"])
def receive_data():
    try:
        data = request.json
        suhu = data.get("temperature")
        kelembaban = data.get("humidity")
        motion = data.get("motion")

        if suhu is None or kelembaban is None:
            return jsonify({"error": "Data tidak lengkap"}), 400

        # Simpan ke MongoDB
        data_entry = {
            "temperature": suhu,
            "humidity": kelembaban,
            "motion": motion,
            "timestamp": datetime.utcnow()
        }
        inserted = collection.insert_one(data_entry)

        return jsonify({"message": "Data berhasil disimpan", "id": str(inserted.inserted_id)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====== JALANKAN SERVER DI 2 IP ======
def run_server(host, port):
    app.run(host=host, port=port, debug=True, use_reloader=False)

if __name__ == '__main__':
    # Jalankan Flask di dua IP sekaligus menggunakan threading
    thread1 = threading.Thread(target=run_server, args=("127.0.0.1", 5000))  # Localhost
    thread2 = threading.Thread(target=run_server, args=(local_ip, 5000))  # IP lokal

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
