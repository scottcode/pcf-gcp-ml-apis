# pcf-gcp-ml-apis
Access to Google Cloud APIs provided from endpoints in Pivotal Cloud Foundry.

## Python dependencies:

`pip install --upgrade google-cloud`

## Cloud Foundry setup

    cf push --no-start
    cf create-service google-ml-apis default google-ml
    cf bind-service google-api-service google-ml -c '{"role": "viewer"}'
    cf start APP_NAME


## Test NLP with curl:

`curl --data '{"content": "New Yorkers will choose one of five finalists for residents in all five boroughs to read as part of a city program."}' http://google-api-service.apps.pcfongcp.com/nlp`

## Test Vision with curl

Run from root directory of repo, because the command refers to the test JSON 
request included in the tests directory.

`curl -d @tests/vision_request.json http://google-api-service.apps.pcfongcp.com/vision`