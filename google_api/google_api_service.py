import os

from flask import Flask, request, jsonify
import helper_functions

app = Flask(__name__)

@app.route("/")
def main():
    return "Hello World!"

@app.route('/api', methods=['POST','OPTIONS'])
@helper_functions.crossdomain(origin='*')
def handle_google_api_request():
    req = request.get_json(force=True)
    return jsonify(req)


@app.route('/nlp', methods=['POST','OPTIONS'])
@helper_functions.crossdomain(origin='*')
def handle_nlp_request():
    req = request.get_json(force=True)
    first_entity_string = helper_functions.first_entity_str(req['content'])
    return jsonify({
        'first_entity_string': first_entity_string
    })


if __name__ == "__main__":
    if os.environ.get('VCAP_SERVICES') is None: # running locally
        PORT = 5000
        DEBUG = True
        app.run(debug=DEBUG)
    else:                                       # running on CF
        PORT = int(os.getenv("PORT"))
        DEBUG = False
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG)

