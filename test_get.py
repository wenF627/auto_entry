import requests


def test_get_request():
    api_url = "http://139.224.207.21:8085/t86CustomsClearanceNetchb/queryList"  # Replace with your API URL

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            print("GET request successful!")
            print("Response data:", data)
            return data
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    test_get_request()
