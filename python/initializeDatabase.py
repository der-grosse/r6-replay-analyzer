import requests as rq
from vars import PORT, BASE_PATH

url = f"http://localhost:{PORT}/{BASE_PATH}/initialize"

response = rq.post(url)
print(f"Response Status Code: {response.status_code}\nResponse Body: {response.text}\n")