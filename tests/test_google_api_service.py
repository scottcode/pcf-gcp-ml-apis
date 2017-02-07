#from parent directory pcf-gcp-ml-apis run:
#python -m unittest pcf-gcp-ml-apis.tests.test_google_api_service
import unittest
import google_api.google_api_service as google_app
import json

class Test(unittest.TestCase):

    def setUp(self):
        self.app = google_app.app.test_client()
        self.app.testing = True

    def test_main_page(self):
        """Test that the status code 200 is returned for get."""
        results = self.app.get("/")
        self.assertEqual(results.status_code,200)

    def test_nlp_status(self):
        """Test that the status code 200 is returned for post."""
        results = self.app.post('/nlp',data=json.dumps({"content":"test data content."}))
        self.assertEqual(results.status_code,200)

    #curl --data '{"content": "New Yorkers will choose one of five finalists for residents in all five boroughs to read as part of a city program."}' http://google-api-service.apps.pcfongcp.com/nlp"""
    # returns{"first_entity_string": "PERSON: New Yorkers"}
    def test_nlp_entity_string_results(self):
        """Test that the nlp app returns the correct entity string"""
        content="New Yorkers will choose one of five finalists for residents in all five boroughs to read as part of a city program."
        results = self.app.post('/nlp',data=json.dumps({"content":content}))
        prediction = '{\n  "first_entity_string": "PERSON: New Yorkers"\n}\n'
        self.assertEqual(results.get_data(as_text=True),prediction)