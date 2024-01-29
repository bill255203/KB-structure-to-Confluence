import requests
from requests.auth import HTTPBasicAuth
import json

# 取得 Confluence 的 API 權杖
API_TOKEN = "ATATT3xFfGF0DwrPrAruGWy2MNmAhiV1_wDegmTSR_dzLHZyv-FFKmLzkb1owiawQ2SliPrUKysDSBh8E57JRXQLve1mlhA9MPFqeq3V2NCl0XJxrmf373v5rm1vZHN63tW3sc2XZemNfzQSRTieMBftG2KaLBrFlHHBkCuV3sTIGUT1uFkmbco=FE4AE7FF"

url = "https://cloudmile4service.atlassian.net/wiki/api/v2/pages"

auth = HTTPBasicAuth("bill.liao@mile.cloud", API_TOKEN)

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "spaceId": "2036072466",
  "status": "current",
  "title": "bll",
  "parentId":"2038890589",
  "body": {
    "representation": "storage",
    "value": "va"
  }
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
response_data = json.loads(response.text)  # Parse the JSON response
page_id = response_data.get('id')  # Get the 'id' field from the response

if page_id:
    print(f"The ID of the created page is: {page_id}")