from apimrt import clouds
from apimrt.cloud_meta import cloud_register
from cloud_detect import provider
import requests
import logging


PROVIDER_TIMEOUT = 60

def get_cloud_provider():
    cloud_provider = provider(timeout=PROVIDER_TIMEOUT)
    if cloud_provider == 'unknown':
        return 'cc3'
    return cloud_provider


def get_cloud_obj():
    cloud_provider = get_cloud_provider()
    return cloud_register.clouds_factory[cloud_provider]()

