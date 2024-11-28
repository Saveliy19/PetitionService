import logging
import json
import time
import requests

logger = logging.getLogger('master_logger')
logger.setLevel(logging.INFO) 

formatter = logging.Formatter('%(filename)s:%(lineno)d - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

class HTTPHandler(logging.Handler):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.labels = '{"job": "petition_service"}'

    def emit(self, record):
        message = self.format(record)
        timestamp = str(int(time.time() * 1e9))  # Время в наносекундах

        payload = {
            "streams": [
                {
                    "stream": json.loads(self.labels),
                    "values": [
                        [timestamp, message]
                    ]
                }
            ]
        }

        try:
            response = requests.post(self.url, json=payload)
            if response.status_code != 204:
                print(f"Failed to send log: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending log: {e}")

http_handler = HTTPHandler("http://loki:3100/loki/api/v1/push")
http_handler.setFormatter(formatter)
logger.addHandler(http_handler)
