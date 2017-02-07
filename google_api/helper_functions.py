# -*- coding: utf-8 -*-
import os
import json
from datetime import timedelta
from functools import update_wrapper
from operator import itemgetter
import base64

from flask import make_response, request, current_app
from google.cloud import language
from google.cloud import vision
from google.cloud.vision.image import Image
from google.oauth2.service_account import Credentials


DEFAULT_LIMIT = 10
SERVICE_NAME = 'google-ml-apis'
SERVICE_INSTANCE_NAME = 'google-ml'
CREDENTIALS = None
clients = {
    'nlp': None,
    'vision': None
}
vision_features = {
    v: vision.feature.Feature(v, max_results=10)
    for k, v in vision.feature.FeatureTypes.__dict__.items()
    if not k.startswith('_')
}
entity_annotation_fields = (
    'bounds',
    'description',
    'locale',
    'locations',
    'mid',
    'score'
)


def get_service_instance_dict():
    """Look in VCAP_SERVICES environment variable and get the dict describing
    a specific service and instance of that service.
    """
    vc_svcs_str = os.environ.get('VCAP_SERVICES')
    if vc_svcs_str is None:
        raise Exception('VCAP_SERVICES not found in environment variables (necessary for credentials)')
    vc_svcs_dict = json.loads(vc_svcs_str)
    svcs = filter(
        lambda s: s.get('name') == SERVICE_INSTANCE_NAME
        , vc_svcs_dict[SERVICE_NAME]
    )
    if not svcs:
        raise Exception(
            "No services matching {targ}. Options: {avail}".format(
                targ=SERVICE_INSTANCE_NAME,
                avail=tuple(map(itemgetter('name'), vc_svcs_dict[SERVICE_NAME]))
            )
        )
    return svcs[0]


def get_google_cloud_credentials():
    """Returns oauth2 credentials of type
    google.oauth2.service_account.Credentials
    """
    global CREDENTIALS
    if CREDENTIALS is None:
        service_info = get_service_instance_dict()
        pkey_data = base64.decodestring(service_info['credentials']['PrivateKeyData'])
        pkey_dict = json.loads(pkey_data)
        CREDENTIALS = Credentials.from_service_account_info(pkey_dict)
    return CREDENTIALS


def get_nlp_client():
    global clients
    if clients.get('nlp') is None:
        clients['nlp'] = language.Client(get_google_cloud_credentials())
    return clients['nlp']


def get_vision_client():
    global clients
    if clients.get('vision') is None:
        service_info = get_service_instance_dict()
        project_id = service_info['credentials']['ProjectId']
        clients['vision'] = vision.Client(
            project=project_id,
            credentials=get_google_cloud_credentials()
        )
    return clients['vision']


def get_text_entities(text):
    client = get_nlp_client()
    doc = client.document_from_text(text)
    return doc.analyze_entities()


def entity_to_str(entity):
    return "{}: {}".format(entity.entity_type, entity.name)


def first_entity_str(text):
    entities = get_text_entities(text)
    if entities:
        entity = entities[0]
        return entity_to_str(entity)
    else:
        return ''


## Vision: Funcs to get labels

def get_image_labels_from_url(image_url, limit=DEFAULT_LIMIT):
    """
    :param image_url: str URL
    :param limit: int Max number of results to return
    :return: list of `google.cloud.vision.entity.EntityAnnotation` instances
    """
    image = Image(get_vision_client(), source_uri=image_url)
    return image.detect_labels(limit=limit)


def get_image_labels_from_bytes(image_bytes, limit=DEFAULT_LIMIT):
    """
    :param image_bytes: str image bytes
    :param limit: int Max number of results to return
    :return: list of `google.cloud.vision.entity.EntityAnnotation` instances
    """
    image = Image(get_vision_client(), content=image_bytes)
    return image.detect_labels(limit=limit)


def get_image_labels_from_base64(image_base64, limit=DEFAULT_LIMIT):
    image_bytes = base64.urlsafe_b64decode(str(image_base64))
    return get_image_labels_from_bytes(image_bytes, limit=limit)


def get_image_labels(image, limit=DEFAULT_LIMIT):
    """
    :param image: str image URL or bytes
    :param limit: int Max number of results to return
    :return: list of `google.cloud.vision.entity.EntityAnnotation` instances
    """
    if isinstance(image, basestring) and image.lower().startswith('http'):
        return get_image_labels_from_url(image, limit=limit)
    else:
        return get_image_labels_from_bytes(image, limit=limit)


def entity_annotation_to_dict(entity_annotation):
    """

    :param entity_annotation: type `google.cloud.vision.entity.EntityAnnotation`
    :return:
    """
    return {
        field: getattr(entity_annotation, field)
        for field in entity_annotation_fields
    }


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
