import requests
from requests.auth import HTTPBasicAuth
import json

# 取得 Confluence 的 API 權杖
API_TOKEN = "ATATT3xFfGF0sUApFrapeATl1h1UmhByXdJwwNl7Mx2-cPux5CJgn_mdrY97O2KzoGJFPMQfuIJXVVOsrJ4QYqrwY1ZYOaLgXh6DnWq24xCykeMzS1WVasXjIjRJdN7J931hIP6-pkET87bioOxh98ggzFIBbPLriWFYCvNJxyLoKX4GQFdlzwo=5002167D"

# 建立請求 
versionUrl = "https://cloudmile4service.atlassian.net/wiki/rest/api/content/2034106516/version" # 取得 version number 的 endpoint
url = "https://cloudmile4service.atlassian.net/wiki/rest/api/content/2034106516" # 更新 page 內容的 endpoint

auth = HTTPBasicAuth("bill.liao@mile.cloud", API_TOKEN)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

file = open('content.json', "r")
content = json.loads(file.read())

# 取得當前 version
VersionResponse = requests.request(
   "GET",
   versionUrl,
   headers=headers,
   auth=auth
)



# 準備修改文章的 json
jsonBody = json.loads(VersionResponse.content)
oldVersionNumber = jsonBody["results"][0]["number"]
content["version"]["number"] = oldVersionNumber + 1 # 把當前的版本 + 1
print(content["version"]["number"])
NewPageContent = json.dumps(content)

response = requests.request(
    "PUT",
    url,
    data=NewPageContent,
    headers=headers,
    auth=auth
)

print(json.dumps(json.loads(response.text),
      sort_keys=True, indent=4, separators=(",", ": ")))
