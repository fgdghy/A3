import os, base64, json, time, requests
from flask import Flask, request, jsonify, make_response
##################
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

BOOK_SERVICE_URL = os.environ.get('URL_BASE_BOOK', 'http://book-service:3000').rstrip('/')
CUSTOMER_SERVICE_URL = os.environ.get('URL_BASE_CUSTOMER', 'http://customer-service:3000').rstrip('/')

def verify_jwt(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    try:
        token = auth_header.split(" ")[1]
        payload = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "==").decode("utf-8"))
        if payload.get("iss") != "cmu.edu" or "sub" not in payload or payload.get("exp", 0) < time.time():
            return None
        return payload
    except: return None

@app.route('/status')
def status(): 
    return "OK", 200

@app.route('/books', methods=['GET', 'POST'], defaults={'p': ''})
@app.route('/books/<path:p>', methods=['GET', 'PUT'])
@app.route('/customers', methods=['GET', 'POST'], defaults={'p': ''})
@app.route('/customers/<path:p>', methods=['GET'])
def web_proxy(p=""):
    auth = request.headers.get('Authorization')
    if not verify_jwt(auth):
        return jsonify({"message": "Unauthorized"}), 401

    if request.path.startswith('/books'):
        base_url = BOOK_SERVICE_URL
    elif request.path.startswith('/customers'):
        base_url = CUSTOMER_SERVICE_URL
    else:
        return jsonify({"message": "Service not found"}), 404

    target_url = f"{base_url}{request.full_path}"
    
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            json=request.get_json(silent=True),
            headers={'Authorization': auth, 'X-Client': 'web'},
            timeout=10
        )
        return make_response(resp.content, resp.status_code)
    except Exception as e:
        print(f"Proxy Error: {str(e)}")
        return jsonify({"message": "Backend error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)