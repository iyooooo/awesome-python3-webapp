import requests

for x in range(0,1):
	r = requests.get('http://127.0.0.1:9000')
	print('%s\n type-----:%s\n\n dict-----:%s' % (requests, type(requests), requests.__dict__.keys()))