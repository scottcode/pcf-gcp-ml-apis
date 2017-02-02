# -*- coding: utf-8 -*-
import os
import json
from datetime import timedelta
from functools import update_wrapper
from operator import itemgetter
import base64

from flask import make_response, request, current_app
import google.cloud.client
import google.cloud.credentials
from google.cloud import language
from google.cloud import vision
from google.oauth2.service_account import Credentials


SERVICE_NAME = 'google-ml-apis'
SERVICE_INSTANCE_NAME = 'google-ml'
CREDENTIALS = None
clients = {
    'nlp': None,
    'vision': None
}


def get_service_instance_dict():
    pass


def get_google_cloud_credentials():
    """Returns oauth2 credentials of type
    google.oauth2.service_account.Credentials
    """
    global CREDENTIALS
    if CREDENTIALS is None:
        vc_svcs_str = os.environ.get('VCAP_SERVICES')
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
        pkey_data = base64.decodestring(svcs[0]['credentials']['PrivateKeyData'])
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
        clients['vision'] = vision.Client(
            project=None, ##TODO: dynamically insert project ID here
            credentials=get_google_cloud_credentials()
        )
    return clients['vision']


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
