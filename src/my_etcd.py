import os
import json
import etcd3

from datetime import datetime as dt, timedelta
from aion.logger import lprint


class MyEtcd():
    default_etcd_host = "titaniadb"
    default_etcd_port = "2379"
    alive_status_index = "0"
    dead_status_index = "1"

    def __init__(self):
        self.host = os.environ.get("ETCD_HOST", self.default_etcd_host)
        self.port = int(os.environ.get("ETCD_PORT", self.default_etcd_port))
        self._connect()

    def get_alive_my_pods(self, device_name):
        prefix_key = "/Pod/" + device_name + "/" + self.alive_status_index
        return self.client.get_prefix(prefix_key)

    def get_disabled_resources(self):
        disabled_resources = []
        for kv_value, kv_metadata in list(self.client.get_prefix("/")):
            key = kv_metadata.key.decode('utf-8')
            if "/" + self.dead_status_index in key:
                update_at = json.loads(kv_value.decode('utf-8'))["updateAt"]
                disabled_resources.append((key, update_at))
        return disabled_resources

    def add_device(self, device_name, my_node):
        key = "/Device/" + device_name + "/" + self.alive_status_index
        if self._is_alive(key) is None:
            self.client.put(key, json.dumps(my_node))
            lprint(f"success to add device: {key}")

    def add_pod(self, device_name, pod_name, my_pod):
        key = "/Pod/" + device_name + "/" + self.alive_status_index + "/" + pod_name
        if self._is_alive(key) is None:
            self.client.put(key, json.dumps(my_pod))
            lprint(f"success to add pod: {key}")

    def disable_pod(self, device_name, pod_name, my_pod, datetime_fmt):
        before_key = "/Pod/" + device_name + "/" + self.alive_status_index + "/" + pod_name
        self.client.delete(before_key)

        # change status 0 -> 1
        my_pod["status"] = self.dead_status_index
        my_pod["updateAt"] = dt.now().strftime(datetime_fmt)
        after_key = "/Pod/" + device_name + "/" + self.dead_status_index + "/" + pod_name
        self.client.put(after_key, json.dumps(my_pod))
        lprint(f"disabled status: {before_key} -> {after_key}")

    def delete_disabled_resource(self, update_at: timedelta, delete_moratorium: timedelta, key):
        if (dt.now() - update_at) > delete_moratorium:
            self.client.delete(key)
            lprint(f"success to delete {key}")

    def _connect(self):
        self.client = etcd3.client(host=self.host, port=self.port)

    def _is_alive(self, key):
        value, _ = self.client.get(key)
        return value
