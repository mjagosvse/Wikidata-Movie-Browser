import requests
import logging


class SparqlEndpoint:
    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url

    def eval_response(self, resp):
        return resp['head']['vars'], resp["results"]["bindings"]

    def request(self, query, retries=2):
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
        }
        params = {
            'query': query
        }
        status, resp = -1, None
        for r in range(retries):
            resp = requests.get(self.endpoint_url, params=params, headers=headers, verify=False)
            if resp.status_code == 200:
                break
            else:
                logging.debug(f'Request failed with status code {resp.status_code} and response {resp.text}')
        else:
            raise Exception(f'Request failed with status code {resp.status_code} and response {resp.text}')

        return self.eval_response(resp.json())
