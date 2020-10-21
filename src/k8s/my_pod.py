from datetime import datetime as dt
from kubernetes import client
from k8s.my_kubernetes import MyKubernetes


class MyPod(MyKubernetes):
    def __init__(self, kube_client: client.CoreV1Api, node_name, datetime_fmt):
        super().__init__(kube_client, node_name, datetime_fmt)
        self.pod_names = []
        self.current_index = 0
        self._fetch_names()

    def __iter__(self):
        return self

    def __next__(self):
        if self.current_index >= len(self.pod_names):
            raise StopIteration

        self.name = self.pod_names[self.current_index]
        pod = self.kube_client.read_namespaced_pod(self.name, self.project_symbol)
        self.current_index = self.current_index + 1

        # remove additional string from docker registry
        image_name = pod.spec.containers[0].image.split('/')[-1].split(':')[0]

        return {
            "podName": self.name,
            "imageName": image_name,
            "deviceNameFk": self.node_name,
            "deployedAt": pod.status.start_time.strftime(self.datetime_fmt),
            "currentVersion": "1.00",
            "latestVersion": "2.00",
            "status": "0",  # always true
            "updateAt": dt.now().strftime(self.datetime_fmt),
        }

    def _fetch_names(self):
        for pod in self.kube_client.list_namespaced_pod(self.project_symbol).items:
            self.pod_names.append(pod.metadata.name)
