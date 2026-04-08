import os
import time
import requests
import mysql.connector
from flask import Flask, request, jsonify, make_response
from collections import OrderedDict
##################
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.json.sort_keys = False

DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER', 'admin'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME', 'books_db') 
}

RECOMMENDATION_SERVICE_URL = os.environ.get('URL_BASE_RECOMMENDATION')
CB_STATE_FILE = "/data/circuit-breaker/state.txt" 

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def validate_price(price):
    try:
        p = float(price)
        if p < 0: 
            return False, None
        s_price = str(price)
        if '.' in s_price and len(s_price.split('.')[-1]) > 2: 
            return False, None
        return True, p
    except: 
        return False, None

def generate_summary(title, author):
    prompt = f"Provide a detailed 500-word summary of the book '{title}' by {author}."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post("", json=payload, timeout=5)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        pass
    return ("This is a comprehensive summary of the book. ")

def format_book(row, include_summary=False):
    res = OrderedDict()

    res["ISBN"] = str(row.get('ISBN') or row.get('isbn'))
    res["title"] = str(row.get('title'))
    res["Author"] = str(row.get('Author') or row.get('author'))
    res["description"] = str(row.get('description'))
    res["genre"] = str(row.get('genre'))
    res["price"] = float(row.get('price'))
    res["quantity"] = int(row.get('quantity'))
    
    if include_summary:
        res["summary"] = str(row.get('summary', ""))
        
    return res

def get_circuit_state():
    if not os.path.exists(CB_STATE_FILE):
        return False, 0
    with open(CB_STATE_FILE, "r") as f:
        try:
            last_fail = float(f.read().strip())
            if (time.time() - last_fail) < 60:
                return True, last_fail
            return False, last_fail
        except:
            return False, 0

def open_circuit():
    os.makedirs(os.path.dirname(CB_STATE_FILE), exist_ok=True)
    with open(CB_STATE_FILE, "w") as f:
        f.write(str(time.time()))

def close_circuit():
    if os.path.exists(CB_STATE_FILE):
        os.remove(CB_STATE_FILE)

@app.route('/status', methods=['GET'])
def status():
    return make_response("OK", 200)

@app.route('/books/<isbn>/related-books', methods=['GET'])
def get_related_books(isbn):
    is_open, last_fail = get_circuit_state()

    if is_open:
        return jsonify({"message": "Service Unavailable"}), 503

    try:
        response = requests.get(
            f"{RECOMMENDATION_SERVICE_URL}/recommended-titles/isbn/{isbn}",
            timeout=3.0
        )
        
        if response.status_code == 204:
            return '', 204
            
        response.raise_for_status()
        
        close_circuit()
        return jsonify(response.json()), 200

    except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        was_half_open = (last_fail > 0) 
        
        open_circuit()
        
        if was_half_open:
            return jsonify({"message": "Service Unavailable"}), 503
        else:
            return jsonify({"message": "Gateway Timeout"}), 504

    except Exception as e:
        print(f"DEBUG: Internal Error: {str(e)}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route('/books', methods=['GET', 'POST'])
def manage_books():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        data = request.get_json() or {}
        req = ['ISBN', 'title', 'Author', 'description', 'genre', 'price', 'quantity']
        if not all(k in data for k in req):
            return jsonify({"message": "Illegal, missing, or malformed input"}), 400
        
        isbn = data['ISBN']
        v_price, p_val = validate_price(data['price'])
        if not v_price: return jsonify({"message": "Illegal, missing, or malformed input"}), 400
        
        cursor.execute("SELECT ISBN FROM books WHERE ISBN = %s", (isbn,))
        if cursor.fetchone():
            return jsonify({"message": "This ISBN already exists in the system."}), 422

        summary = generate_summary(data['title'], data['Author'])
        cursor.execute("INSERT INTO books (ISBN, title, Author, description, genre, price, quantity, summary) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
                       (isbn, data['title'], data['Author'], data['description'], data['genre'], p_val, data['quantity'], summary))
        conn.commit()

        res = {"ISBN": isbn, "title": data['title'], "Author": data['Author'], "description": data['description'], "genre": data['genre'], "price": p_val, "quantity": data['quantity']}
        resp = make_response(jsonify(res), 201)
        resp.headers['Location'] = f"/books/{isbn}"
        return resp
    else:
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
        return jsonify([format_book(b, include_summary=True) for b in rows]), 200

@app.route('/books/<isbn>', methods=['GET', 'PUT'])
@app.route('/books/isbn/<isbn>', methods=['GET'])
def handle_book(isbn):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'PUT':
        data = request.get_json() or {}
        req = ['ISBN', 'title', 'Author', 'description', 'genre', 'price', 'quantity']
        if not all(k in data for k in req) or str(data['ISBN']) != str(isbn):
            return jsonify({"message": "Illegal, missing, or malformed input"}), 400
        
        v_price, p_val = validate_price(data['price'])
        if not v_price: return jsonify({"message": "Illegal, missing, or malformed input"}), 400
        
        cursor.execute("SELECT * FROM books WHERE ISBN = %s", (isbn,))
        if not cursor.fetchone(): 
            return jsonify({"message": "ISBN not found"}), 404
        
        cursor.execute("UPDATE books SET title=%s, Author=%s, description=%s, genre=%s, price=%s, quantity=%s WHERE ISBN=%s", 
                       (data['title'], data['Author'], data['description'], data['genre'], p_val, data['quantity'], isbn))
        conn.commit()
        return jsonify(format_book({"ISBN": isbn, "title": data['title'], "Author": data['Author'], "description": data['description'], "genre": data['genre'], "price": p_val, "quantity": data['quantity']})), 200
    else:
        cursor.execute("SELECT * FROM books WHERE ISBN = %s", (isbn,))
        res = cursor.fetchone()
        if not res: 
            return jsonify({"message": "ISBN not found"}), 404
        return jsonify(format_book(res, include_summary=True)), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)