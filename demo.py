import requests
import json


def fetch_properties():
    url = "https://retailapis-in.geoiq.ai/bdapp/prod/v1/bd/getAllKissflowProperties"

    # It is good practice to include a User-Agent or Content-Type for POST requests
    headers = {
        'x-api-key': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJtYWlsSWRlbnRpdHkiOiJsZW5za2FydC1hZG1pbkBnZW9pcS5pbyJ9.SbaX7dGyaRz_EVwgdE-cQe7_c0pCnM2OPJD2legV0jU',
        'Content-Type': 'application/json'
    }

    payload = {}  # Changed to a dict, though it remains empty per your example

    try:
        # Making the POST request
        response = requests.post(url, headers=headers, json=payload)

        # Check if the request was successful (status code 200)
        response.raise_for_status()

        # Try to parse and print the JSON response nicely
        data = response.json()
        print(json.dumps(data, indent=4))

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")


if __name__ == "__main__":
    fetch_properties()