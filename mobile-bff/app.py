import os, base64, json, time, requests
from flask import Flask, request, jsonify, make_response
##################
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.json.sort_keys = False 

BOOK_SERVICE_URL = os.environ.get('URL_BASE_BOOK', 'http://book-service:3000').rstrip('/')
CUSTOMER_SERVICE_URL = os.environ.get('URL_BASE_CUSTOMER', 'http://customer-service:80').rstrip('/')

def verify_jwt(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "): return None
    try:
        token = auth_header.split(" ")[1]
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
        if payload.get("iss") != "cmu.edu" or payload.get("exp", 0) < time.time():
            return None
        return payload
    except: return None

def transform_data(path, method, data):
    if not isinstance(data, (dict, list)): return data

    if "books" in path and method == "GET":
        def fix_book(b):
            if isinstance(b, dict) and b.get("genre") == "non-fiction":
                b["genre"] = 3
            return b
        if isinstance(data, list): return [fix_book(item) for item in data]
        return fix_book(data)

    if "customers" in path and method == "GET":
        to_del = ["address", "address2", "city", "state", "zipcode"]
        def filter_cust(c):
            if isinstance(c, dict):
                for attr in to_del: c.pop(attr, None)
            return c
        if isinstance(data, list): return [filter_cust(item) for item in data]
        return filter_cust(data)
    
    return data

@app.route('/status')
def status(): 
    """Task 1: K8S Liveness Probe 必需的接口 """
    return make_response("OK", 200, {"Content-Type": "text/plain"})

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    client_type = request.headers.get('X-Client-Type')
    if not client_type:
        return jsonify({"message": "X-Client-Type header is mandatory"}), 400

    auth = request.headers.get('Authorization')
    if not verify_jwt(auth):
        return jsonify({"message": "Unauthorized"}), 401

    if path.startswith('books'):
        target_base = BOOK_SERVICE_URL
    elif path.startswith('customers'):
        target_base = CUSTOMER_SERVICE_URL
    else:
        return jsonify({"message": "Service not found"}), 404

    target_url = f"{target_base}/{path}"
    if request.query_string:
        target_url += f"?{request.query_string.decode()}"
    
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            json=request.get_json(silent=True),
            headers={'Authorization': auth, 'X-Client-Type': client_type},
            timeout=30 
        )

        if resp.status_code in [200, 201]:
            try:
                raw_json = resp.json()
                final_data = transform_data(request.path, request.method, raw_json)
                response = make_response(jsonify(final_data), resp.status_code)

                if 'Location' in resp.headers:
                    base_url = request.url_root.rstrip('/')
                    loc = resp.headers['Location']
                    response.headers['Location'] = f"{base_url}{loc}" if not loc.startswith('http') else loc
                
                return response
            except: 
                pass

        return make_response(resp.content, resp.status_code)
        
    except Exception as e:
        return jsonify({"message": "Backend error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)