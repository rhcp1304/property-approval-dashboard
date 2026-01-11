import requests
url = "https://retailapis-in.geoiq.ai/bdapp/prod/v1/bd/getAllKissflowProperties"
payload = ""
headers = {
  'x-api-key': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJtYWlsSWRlbnRpdHkiOiJsZW5za2FydC1hZG1pbkBnZW9pcS5pbyJ9.SbaX7dGyaRz_EVwgdE-cQe7_c0pCnM2OPJD2legV0jU'
}
response = requests.request("POST", url, headers=headers, data=payload)
print(response.text)
