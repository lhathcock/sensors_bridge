from connect import SESSION

data = {}

response = SESSION.post('http://localhost:6000/welcome', data=data)

if response.status_code == 200:
    print('Sent data to the server')
else:
    print ('Error: ', response.status_code)
    print('Failed to send. Saving it to local file.')
