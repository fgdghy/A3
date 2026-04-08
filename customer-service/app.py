import os
import mysql.connector
import re
import json
from flask import Flask, request, jsonify, make_response
from confluent_kafka import Producer
##################
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER', 'admin'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME', 'customers_db')
}

KAFKA_CONF = {
    'bootstrap.servers': os.environ.get('KAFKA_SERVERS', 'localhost:9092')
}
KAFKA_TOPIC = "linyul.customer.evt"
producer = Producer(KAFKA_CONF)

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def is_valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", str(email)))

@app.route('/status', methods=['GET'])
def status():
    resp = make_response("OK", 200)
    resp.headers['Content-Type'] = 'text/plain'
    return resp

@app.route('/customers', methods=['GET', 'POST'])
def handle_customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        data = request.get_json() or {}
        req = ['userId', 'name', 'phone', 'address', 'city', 'state', 'zipcode']
        
        if not all(k in data for k in req):
            return jsonify({"message": "Illegal, missing, or malformed input"}), 400
        
        uid = data['userId']
        if not is_valid_email(uid):
            return jsonify({"message": "Illegal, missing, or malformed input"}), 400
            
        if len(str(data['state'])) != 2:
            return jsonify({"message": "Illegal, missing, or malformed input"}), 400
        
        cursor.execute("SELECT id FROM customers WHERE userId = %s", (uid,))
        if cursor.fetchone():
            return jsonify({"message": "This user ID already exists in the system."}), 422
        
        addr2 = data.get('address2', "")
        cursor.execute("INSERT INTO customers (userId, name, phone, address, address2, city, state, zipcode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
                       (uid, data['name'], data['phone'], data['address'], addr2, data['city'], data['state'], data['zipcode']))
        new_id = cursor.lastrowid
        conn.commit()
        
        data['id'] = int(new_id)
        data['address2'] = addr2

        try:
            producer.produce(KAFKA_TOPIC, json.dumps(data).encode('utf-8'))
            producer.flush()
        except Exception as e:
            print(f"Failed to send Kafka message: {e}")

        resp = make_response(jsonify(data), 201)
        resp.headers['Location'] = f"/customers/{new_id}"
        return resp
    
    else:
        uid = request.args.get('userId')
        if not uid or not is_valid_email(uid):
            return jsonify({"message": "Illegal, missing, or malformed input"}), 400
            
        cursor.execute("SELECT * FROM customers WHERE userId = %s", (uid,))
        res = cursor.fetchone()
        if not res:
            return jsonify({"message": "User-ID does not exist in the system"}), 404
            
        return jsonify(res), 200

@app.route('/customers/<path:cust_id>', methods=['GET'])
def get_customer_by_id(cust_id):
    if not str(cust_id).isdigit():
        return jsonify({"message": "Illegal, missing, or malformed input"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE id = %s", (int(cust_id),))
    res = cursor.fetchone()
    if not res:
        return jsonify({"message": "ID does not exist in the system"}), 404
        
    return jsonify(res), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)