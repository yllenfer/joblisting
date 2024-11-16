import logging
import requests
import time
# from logger import LOG


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

valid_methods = ["get", "post", "patch", "put"]


def custom_requests_patch(*args, **kwargs):
    return exponential_backoff(*args, method="patch", **kwargs)

def custom_requests_post(*args, **kwargs):
    return exponential_backoff(*args, method="post", **kwargs)

def custom_requests_get(*args, **kwargs):
    return exponential_backoff(*args, method="get", **kwargs)

def custom_requests_put(*args, **kwargs):
    return exponential_backoff(*args, method="get", **kwargs)


def exponential_backoff(*args, method="get", **kwargs):
    retries, max_retries = 0, 5
    backoff_seconds, max_backoff = 2, 32

    # Validate HTTP method
    if method not in valid_methods:
        LOG.error(f"Invalid method: {method}. Valid methods: {valid_methods}")
        raise ValueError(f"Invalid method: {method}")

    # Make the request
    response = getattr(requests, method)(*args, **kwargs)

    while response.status_code == 429 and retries < max_retries:
        # Adjust backoff time based on server header if available
        if response.headers.get("X-QBAPI-Throttle-TTL"):
            backoff_seconds = min(int(response.headers["X-QBAPI-Throttle-TTL"]), max_backoff)
        else:
            backoff_seconds = min(backoff_seconds * 2, max_backoff)

        LOG.info(f"Attempt {retries + 1}/{max_retries} - Received 429 status, retrying in {backoff_seconds} seconds...")
        time.sleep(backoff_seconds)
        retries += 1
        response = getattr(requests, method)(*args, **kwargs)

    # Handle different status codes
    if response.status_code == 429:
        LOG.error(f"Max retries reached. Request failed with 429 Too Many Requests.")
    elif response.status_code >= 500:
        LOG.error(f"Server error: {response.status_code}.")
    elif response.status_code >= 400:
        LOG.warning(f"Client error: {response.status_code}.")
    else:
        LOG.info(f"Request succeeded with status: {response.status_code}.")

    return response
