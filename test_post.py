import requests


def test_post_request():
    return_api_url = "http://139.224.207.21:8085/t86CustomsClearanceNetchb/netchbConfrim"  # Replace with your API URL

    # Example of a dummy result that would normally be sent
    test_data = {
        "id": "2867",
        "mawbNo": "297-54899320",
        "result": "test success",
        "screenshot": None,
        "declareResult": None,
        "declareResultUrl": None
    }

    try:
        response = requests.post(return_api_url, json=test_data)
        if response.status_code == 200:
            print("POST request successful!")
        else:
            print(f"Failed to send data. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    test_post_request()
