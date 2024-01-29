import requests
from requests.auth import HTTPBasicAuth
import json
from bs4 import BeautifulSoup

# 取得 Confluence 的 API 權杖
API_TOKEN = "ATATT3xFfGF0DwrPrAruGWy2MNmAhiV1_wDegmTSR_dzLHZyv-FFKmLzkb1owiawQ2SliPrUKysDSBh8E57JRXQLve1mlhA9MPFqeq3V2NCl0XJxrmf373v5rm1vZHN63tW3sc2XZemNfzQSRTieMBftG2KaLBrFlHHBkCuV3sTIGUT1uFkmbco=FE4AE7FF"
page_ids = ["2038890562", "2038890589", "2038792431", "2038531289",2036072466]
i = 0

for page_id in page_ids:
    i += 1 
    # 建立請求 
    versionUrl = f"https://cloudmile4service.atlassian.net/wiki/rest/api/content/{page_id}/version" # 取得 version number 的 endpoint
    url = f"https://cloudmile4service.atlassian.net/wiki/rest/api/content/{page_id}" # 更新 page 內容的 endpoint

    auth = HTTPBasicAuth("bill.liao@mile.cloud", API_TOKEN)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    # Construct the filename based on 'i'
    filename = f"{i}.html"
    
    with open(filename, 'r', encoding='utf-8') as html_file:
        htmlobject = html_file.read()

    soup = BeautifulSoup(htmlobject, 'html.parser')
    span_tag = soup.find('span')
    first_a_tag = span_tag.find('a')
    if first_a_tag:
        content = first_a_tag.text
        print(content)
    htmlobject = str(soup)

    # Create a dictionary for the page content
    content = {
        "version": {
            "number": 1,
            "message": "update"
        },
        "title": content,
        "type": "page",
        "body": {
            "storage": {
                "value": htmlobject,
                "representation": "storage"
            }
        }
    }
    print(content)
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

    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
