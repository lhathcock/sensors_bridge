import requests
from urllib.parse import urlencode
from config import USERNAME,PASSWORD, SERVER_LOGIN

# URL-encode the token parameters
params = urlencode(
    {'username': USERNAME, 'password': PASSWORD, 'f': 'json'})
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}
SESSION = requests.Session()
response = SESSION.post(SERVER_LOGIN, data=params, headers=headers)


