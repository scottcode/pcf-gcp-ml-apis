import os

from flask import Flask, request, jsonify
from google.cloud import language, vision
import helper_functions

app = Flask(__name__)


@app.route('/api', methods=['POST','OPTIONS'])
@helper_functions.crossdomain(origin='*')
def handle_google_api_request():
    req = request.get_json(force=True)
    return jsonify(req)


if __name__ == "__main__":
    if os.environ.get('VCAP_SERVICES') is None: # running locally
        PORT = 5000
        DEBUG = True
        app.run(debug=DEBUG)
    else:                                       # running on CF
        PORT = int(os.getenv("PORT"))
        DEBUG = False
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG)

