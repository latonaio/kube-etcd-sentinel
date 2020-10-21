import os
import json
import threading

from time import sleep
from datetime import datetime as dt, timedelta
from kubernetes import client, config
from aion.logger import lprint
from k8s.my_node import MyNode
from k8s.my_pod import MyPod
from my_etcd import MyEtcd


class Controller():
    add_pod_interval = 5
    add_device_interval = 30
    disable_interval = 10
    delete_interval = 10
    datetime_fmt = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        self.controller_list = []
        self.node_name = os.environ.get("MY_NODE_NAME")
        self._set_kube_client()

    def start(self):
        try:
            my_etcd = MyEtcd()
            threading.Thread(target=self._add_device, args=(my_etcd,)).start()
            threading.Thread(target=self._add_pods, args=(my_etcd,)).start()
            threading.Thread(target=self._disable_pods, args=(my_etcd,)).start()
            threading.Thread(target=self._delete_disabled_resources, args=(my_etcd,)).start()

        except Exception as e:
            lprint(f"can't connect with etcd. {e}")

    def _set_kube_client(self):
        if os.path.exists(os.environ.get("HOME") + "/.kube/config"):
            config.load_kube_config()
            self.kube_client = client.CoreV1Api()
        else:
            self.kube_client = client.CoreV1Api(client.ApiClient(self.kube_config))

    def _add_device(self, my_etcd: MyEtcd):
        lprint("start add_device thread...")
        while True:
            try:
                my_node = MyNode(self.kube_client, self.node_name, self.datetime_fmt)
                my_node.fetch()
                my_etcd.add_device(my_node.own["deviceName"], my_node.own)

            except Exception as e:
                lprint(f"can't add_device. {e}")

            finally:
                sleep(self.add_device_interval)

    def _add_pods(self, my_etcd: MyEtcd):
        lprint("start add_pods thread...")
        while True:
            try:
                for p in MyPod(self.kube_client, self.node_name, self.datetime_fmt):
                    my_etcd.add_pod(p["deviceNameFk"], p["podName"], p)

            except Exception as e:
                lprint(f"failed to add_pods. {e}")

            finally:
                sleep(self.add_pod_interval)

    def _disable_pods(self, my_etcd: MyEtcd):
        lprint("start disable_pods thread...")
        while True:
            try:
                for pod_on_etcd, _ in my_etcd.get_alive_my_pods(self.node_name):
                    _pod_on_etcd = json.loads(pod_on_etcd.decode("utf-8"))
                    pod_name_on_etcd = _pod_on_etcd["podName"]

                    is_pod = False
                    for pod_on_kube in MyPod(self.kube_client, self.node_name, self.datetime_fmt):
                        if pod_name_on_etcd == pod_on_kube["podName"]:
                            is_pod = True
                            break

                    if is_pod is False:
                        my_etcd.disable_pod(_pod_on_etcd["deviceNameFk"], pod_name_on_etcd, _pod_on_etcd, self.datetime_fmt)

            except Exception as e:
                lprint(f"failed to disabled_pods. {e}")

            finally:
                sleep(self.disable_interval)

    def _delete_disabled_resources(self, my_etcd: MyEtcd):
        lprint("start delete_disabled_resources thread...")
        delete_moratorium = 60

        while True:
            try:
                for key, update_at in my_etcd.get_disabled_resources():
                    update_at_datetime = dt.strptime(update_at, self.datetime_fmt)
                    my_etcd.delete_disabled_resource(update_at_datetime, timedelta(seconds=delete_moratorium), key)

            except Exception as e:
                lprint(f"failed to delete_disabled_resources. {e}")

            finally:
                sleep(self.delete_interval)

    @property
    def kube_config(self) -> client.Configuration:
        conf = client.Configuration()
        conf.verify_ssl = True
        conf.host = "https://" + os.environ.get("KUBERNETES_SERVICE_HOST")
        conf.api_key_prefix["authorization"] = "Bearer"
        conf.ssl_ca_cert = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
            conf.api_key["authorization"] = f.read()
        return conf
