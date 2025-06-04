import requests

url = 'https://127.0.0.1:5000'

response = requests.get(
    url,
    cert=('./dummyClientCertificates/client.cert', './dummyClientCertificates/client.key'),
    verify='./CAcertificates/ca.cert'  # solo si tienes la CA del servidor
)

print(response.status_code)
print(response.text)
