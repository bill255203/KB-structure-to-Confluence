import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://cloudmile4service.atlassian.net/wiki/api/v2/pages/2044466099"
EMAIL = "bill.liao@mile.cloud"
API_TOKEN = "ATATT3xFfGF0sLJ4nSgF8FFlk-0XUlaYTBUjIx2MwqFLQDVzQ46YiPN2lcCalzGrQ4Vu4acu75gquQSEyBay2pXdOJ5z4mj4uNWnP21zeXaRe4ZXWiTtUe3bro8jVSZTwv5G0jGdDavQOlghePlabFysENgS7ZseNsBp-Gu6011sHphM-w3cZaA=B4157CF9"

auth = HTTPBasicAuth(EMAIL, API_TOKEN)

headers = {
  "Accept": "application/json"
}

response = requests.request(
   "GET",
   url,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))