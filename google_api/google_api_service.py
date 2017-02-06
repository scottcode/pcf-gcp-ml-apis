import os

from flask import Flask, request, jsonify
import helper_functions
from helper_functions import (
    DEFAULT_LIMIT, entity_annotation_to_dict
)

app = Flask(__name__)


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


@app.route('/vision', methods=['POST','OPTIONS'])
@helper_functions.crossdomain(origin='*')
def handle_vision_request():
    """Expecting JSON request as outlined in
    https://cloud.google.com/vision/docs/reference/rest/v1/images/annotate
    """
    req_dict = request.get_json(force=True)
    responses = []
    for req in req_dict['requests']
        # get maxResults for LABEL_DETECTION
        label_feats = [
            feat for feat in req['features'] if feat['type'] == 'LABEL_DETECTION'
        ]
        if label_feats:
            limit = label_feats[0].get('maxResults', DEFAULT_LIMIT)
        else:
            limit = DEFAULT_LIMIT
        if 'content' in req['image']:
            labels = helper_functions.get_image_labels_from_base64(
                req['image']['content'],
                limit
            )
        else:
            labels = []
        responses.append(
            dict(labelAnnotations=list(map(entity_annotation_to_dict, labels)))
        )
    return jsonify(responses)


if __name__ == "__main__":
    if os.environ.get('VCAP_SERVICES') is None: # running locally
        PORT = 5000
        DEBUG = True
        app.run(debug=DEBUG)
    else:                                       # running on CF
        PORT = int(os.getenv("PORT"))
        DEBUG = False
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG)

