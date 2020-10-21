from datetime import datetime as dt
from kubernetes import client
from k8s.my_kubernetes import MyKubernetes


class MyNode(MyKubernetes):
    def __init__(self, kube_client: client.CoreV1Api, node_name, datetime_fmt):
        super().__init__(kube_client, node_name, datetime_fmt)
        self._own = {}

    def fetch(self):
        my_node = self.kube_client.read_node(self.node_name)
        self.own = {
            "deviceIp": my_node.status.addresses[0].address,
            "deviceName": self.node_name,
            "projectSymbolFk": self.project_symbol,
            "os": my_node.status.node_info.os_image,
            "connectionStatus": "0",  # only true. if host is down, we can't get the host info
            "updateAt": dt.now().strftime(self.datetime_fmt),
        }

    @property
    def own(self):
        return self._own

    @own.setter
    def own(self, own):
        self._own = own
