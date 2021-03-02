import requests
import time
import datetime
from requests import Session
import logging

logger = logging.getLogger('root')


class RequestManager():

    def __init__(self, timeout=7, retries=5):
        self.session = Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.session.headers.update({'content-type': 'application/json'})
        self.session.headers.update({'accept': 'application/json'})
        self.timeout = timeout
        self.retries = retries

    def send_request(self, my_request, is_proxies = False):
        max_retries = 7

        def retry():
            self.retries += 1
            if self.retries > max_retries:
                raise Exception("Max retries on %s (%s) hit, raising." % (my_request.url, my_request.data))
            return self.send_request(my_request)

        response = None
        try:
            my_request.headers.update()
            prepped = self.session.prepare_request(my_request)
            proxies = {
                "http": "http://127.0.0.1:1082",
                "https": "https://127.0.0.1:1082"
            }
            if is_proxies is True:
                response = self.session.send(prepped, timeout=7, proxies=proxies)
            else:
                response = self.session.send(prepped, timeout=7)
            response.raise_for_status()


        except requests.exceptions.HTTPError as e:

            if response is None:
                raise e

            logger.error(response.content)


        except requests.exceptions.Timeout as e:
            # Timeout, re-run this request
            logger.warning("Timed out on request: %s (%s), retrying..." % (my_request.url, my_request.data))
            return retry()

        except requests.exceptions.ConnectionError as e:
            logger.warning("Unable to contact the target API (%s). Please check the URL. Retrying. " +
                           "Request: %s %s \n %s" % (e, my_request.url, my_request.data))
            time.sleep(1)
            return retry()

        return response.json()
