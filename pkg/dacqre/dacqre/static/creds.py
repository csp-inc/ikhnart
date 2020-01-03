import os
import ee


def init_creds(service_account='csp-ee@csp-projects.iam.gserviceaccount.com', service_json='/root/service-ee.json'):
    my_service = service_account
    if os.path.isfile(service_json):
        credentials = ee.ServiceAccountCredentials(my_service, service_json)
        ee.Initialize(credentials)
    else:
        ee.Initialize()
