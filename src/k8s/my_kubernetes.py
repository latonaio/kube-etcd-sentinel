import os

from kubernetes import client


class MyKubernetes():
    project_symbol = os.environ.get("PROJECT_SYNMOL", "prj")

    def __init__(self, kube_client: client.CoreV1Api, node_name, datetime_fmt):
        self.kube_client = kube_client
        self.node_name = node_name
        self.datetime_fmt = datetime_fmt
