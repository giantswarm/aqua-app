import yaml
import requests
import time
import json
import subprocess
from functools import partial
import time
import random
import string
import pytest
from pathlib import Path
from typing import Optional
from textwrap import dedent, indent
import socket

import logging
LOGGER = logging.getLogger(__name__)


class TestInstall:

    # @pytest.mark.skip()
    def test_aqua_server(self, kubernetes_cluster, random_namespace):

        kubectl = kubernetes_cluster.kubectl

        # FIXME also put in destination_namespace?
        # then no need for random app_name postfix
        # and everything is in one namespace
        # makes debugging easier

        app_resource_namespace = "app-testing"
        app_destination_namespace = random_namespace
        app_name_suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
        app_version = "5.3-gs1"

        LOGGER.info(f"Destination namespace is {app_destination_namespace}")

        # shortcut function with fixed namespace
        kn = partial(kubernetes_cluster.kubectl, namespace=app_destination_namespace)


        # provide pull-secrets
        registry_auth_quay_secret = Path(__file__).parent / "secrets" / "registry-auth-quay-secret.yaml"
        kubectl("create", namespace=app_destination_namespace, filename=registry_auth_quay_secret)

        # create namespace for app manifests and configmaps
        app_resource_namespace_manifest = yaml.safe_load(dedent(f"""
            apiVersion: v1
            kind: Namespace
            metadata:
              name: {app_resource_namespace}
        """))

        # kubectl("create", filename="-", input=yaml.safe_dump(app_resource_namespace_manifest))
        # "apply" ignores already existing namespace, "create" fails
        kubectl("apply", filename="-", input=yaml.safe_dump(app_resource_namespace_manifest))


        # ## create aqua server

        app_name = f"aqua-app-server-{app_name_suffix}"

        app_data = {
            "name": app_name,
            "name_in_catalog": "aqua-app-server",
            "catalog": "chartmuseum", 
            "version": app_version, 
            "namespace": app_destination_namespace, 
            "app_resource_namespace": app_resource_namespace,
            "values_for_configmap": {
                "imageCredentials": {
                    "create": False,
                    "name": "giantswarm-partner-aqua-pull-secret"
                },
                "db": {
                    "persistence": {
                        "size": "1Gi"
                    }
                }
            }
        }

        kubectl("create", filename="-", input=yaml.safe_dump_all(app_template(**app_data)), output=None)
        LOGGER.info(f"App resource {app_name} created")

        # FIXME hand over kubectl-partial?
        wait_for_rollout(kubernetes_cluster, f"deployment/{app_name}-console", namespace=app_destination_namespace)
        LOGGER.info(f"deployment/{app_name}-console is ready")


        # wait for console api answer
        api_answered = False
        while not api_answered:
            try:
                with kubernetes_cluster.port_forward(f"service/aqua-app-server-{app_name_suffix}-console-svc", 8080, namespace=app_destination_namespace, retries=1) as port:
                    response = requests.get(f"http://localhost:{port}/api")
                    response.raise_for_status()
                    api_response = response.json()
                    # api_response = response.text
                    LOGGER.info(f"api_response: {api_response}")

                    api_answered = "version" in api_response
                    # status_green = efk_health["status"] == "green"

            # except socket.error as e:
            except OSError as e:
                LOGGER.info(f"ConnectionError, will retry: {repr(e)}")
            except Exception as e:
                LOGGER.error(repr(e))
                # ERROR    test_install:test_install.py:135 Exception('kubectl port-forward returned exit code 1')
                # ERROR    test_install:test_install.py:137 JSONDecodeError('Expecting value: line 1 column 1 (char 0)')
            if not api_answered:
                time.sleep(5)

        LOGGER.info(f"console api version: {api_response['version']}")







        # add admin
        # license
        # create scanner user

        try:
            with kubernetes_cluster.port_forward(f"service/aqua-app-server-{app_name_suffix}-console-svc", 8080, namespace=app_destination_namespace, retries=1) as port:

                # set password for admin account
                data = {
                    "username": "administrator",
                    "password": "testtest",
                    "confirmPwd": "testtest",
                    "email": "",
                    "admin": "",
                    "validLicense": True,
                    "role":{
                        "text": "Administrator",
                        "id": "administrator"
                    },
                    "remember": False
                }
                r = requests.post(f"http://localhost:{port}/api/v1/reset_admin", json=data)
                r.raise_for_status()


                # login as admin to get api_token
                data = {
                    "id": "administrator",
                    "password": "testtest",
                    "remember": False
                }
                r = requests.post(f"http://localhost:{port}/api/v1/login", json=data)
                r.raise_for_status()
                api_token = r.json()["token"]

                LOGGER.info(f"api_token: {api_token}")


                # provide license token
                aqua_license_token = Path(Path(__file__).parent / "secrets" / "aqua-license-token").read_text()
                data = {
                    "token": aqua_license_token,
                    "telemetry_enabled": False
                }
                headers = {"Authorization": f"Bearer {api_token}"}
                r = requests.post(f"http://localhost:{port}/api/v2/license", headers=headers, json=data)
                r.raise_for_status()
                

                # read features
                # FIXME how to check for valid license?
                headers = {"Authorization": f"Bearer {api_token}"}
                r = requests.get(f"http://localhost:{port}/api/v2/features", headers=headers)
                r.raise_for_status()
                features = r.json()

                # FIXME assert something here

                LOGGER.info(f"features: {features}")


                # create user account for aqua scanner
                data = {
                    "id": "scanner",
                    "password": "password",
                    "passwordConfirm": "password",
                    "roles": ["Scanner"],
                    "name": "",
                    "email": "",
                    "first_time": False
                }
                headers = {"Authorization": f"Bearer {api_token}"}
                r = requests.post(f"http://localhost:{port}/api/v1/users", headers=headers, json=data)
                r.raise_for_status()

                # FIXME read user and assert
                LOGGER.info(f"user account for aqua scanner created.")

        except OSError as e:
            LOGGER.info(f"ConnectionError, will retry: {repr(e)}")
        except Exception as e:
            LOGGER.error(repr(e))







        # ## create aqua scanner

        app_name = f"aqua-app-scanner-{app_name_suffix}"

        app_data = {
            "name": app_name,
            "name_in_catalog": "aqua-app-scanner",
            "catalog": "chartmuseum", 
            "version": app_version, 
            "namespace": app_destination_namespace, 
            "app_resource_namespace": app_resource_namespace,
            "values_for_configmap": {
                "user": "scanner",
                "password": "password",
                "server": {
                    "serviceName": f"aqua-app-server-{app_name_suffix}-console-svc"
                },
                "serviceAccount": f"aqua-app-server-{app_name_suffix}-sa"
            }
        }

        kubectl("create", filename="-", input=yaml.safe_dump_all(app_template(**app_data)), output=None)
        LOGGER.info(f"App resource {app_name} created")

        wait_for_rollout(kubernetes_cluster, f"deployment/{app_name}-scanner", namespace=app_destination_namespace)
        LOGGER.info(f"deployment/{app_name}-scanner is ready")





        # ## create aqua enforcer

        try:
            with kubernetes_cluster.port_forward(f"service/aqua-app-server-{app_name_suffix}-console-svc", 8080, namespace=app_destination_namespace, retries=1) as port:

                headers = {"Authorization": f"Bearer {api_token}"}
                r = requests.get(f"http://localhost:{port}/api/v1/servers", headers=headers)
                r.raise_for_status()
                api_result = r.json()
                gateway_ids = [gateway["id"] for gateway in api_result]

                LOGGER.info(f"Gateway IDs: {', '.join(gateway_ids)}")


                data = {
                    "allowed_labels": [],
                    "allowed_registries": [],
                    "allowed_secrets": [],
                    "audit_failed_login": True,
                    "audit_success_login": True,
                    "container_activity_protection": False,
                    "enforce": False,
                    "description": "",
                    "gateways": gateway_ids,
                    "host_os": "Linux",
                    "hostname": "testgroup",
                    "id": "testgroup",
                    "image_assurance": True,
                    "logicalname": "testgroup",
                    "network_protection": False,
                    "orchestrator": {
                        "type": "kubernetes",
                        "service_account": f"aqua-app-server-{app_name_suffix}-sa",
                        "namespace": app_destination_namespace
                    },
                    "runtime_type": "docker",
                    "sync_host_images": True,
                    "syscall_enabled": False,
                    "token": "",
                    "type": "agent",
                    "user_access_control": False,
                    "allowed_labels_temp": [],
                    "allowed_registries_temp": [],
                    "allowed_secrets_temp": [],
                    "risk_explorer_auto_discovery": False,
                    "allow_kube_enforcer_audit": True,
                    "auto_discovery_enabled": True,
                    "auto_discover_configure_registries": True,
                    "auto_scan_discovered_images_running_containers": True,
                    "admission_control": True,
                    "block_admission_control": False,
                    "micro_enforcer_injection": True,
                    "micro_enforcer_image_name": "",
                    "micro_enforcer_secrets_name": "",
                    "auto_copy_secrets": False,
                    "micro_enforcer_certs_secrets_name": "",
                    "kube_bench_image_name": "",
                    "runtime_policy_name": "",
                    "host_protection": False,
                    "host_network_protection": False,
                    "enforcer_image_name": "registry.aquasec.com/enforcer:5.3.20350"
                }
                headers = {"Authorization": f"Bearer {api_token}"}
                r = requests.post(f"http://localhost:{port}/api/v1/hostsbatch", headers=headers, json=data)
                r.raise_for_status()
                api_result = r.json()
                enforcer_token = api_result.get("token")

                LOGGER.info(f"Enforcer token: {enforcer_token}")

        except OSError as e:
            LOGGER.info(f"ConnectionError, will retry: {repr(e)}")
        except Exception as e:
            LOGGER.error(repr(e))







        app_name = f"aqua-app-enforcer-{app_name_suffix}"

        app_data = {
            "name": app_name,
            "name_in_catalog": "aqua-app-enforcer",
            "catalog": "chartmuseum", 
            "version": app_version, 
            "namespace": app_destination_namespace, 
            "app_resource_namespace": app_resource_namespace,
            "values_for_configmap": {
                "enforcerToken": enforcer_token,
                "enforcerLogicalName": "testgroup",
                "gate": {
                    "host": f"aqua-app-server-{app_name_suffix}-gateway-svc"
                }
            }
        }

        kubectl("create", filename="-", input=yaml.safe_dump_all(app_template(**app_data)), output=None)
        LOGGER.info(f"App resource {app_name} created")

        wait_for_rollout(kubernetes_cluster, f"daemonset/{app_name}-ds", namespace=app_destination_namespace)
        LOGGER.info("aqua-enforcer-ds is ready")


        # k(f"delete app aqua-app-enforcer-{app_name_suffix}", namespace=app_resource_namespace, output=None)
        # k(f"delete app aqua-app-scanner-{app_name_suffix}", namespace=app_resource_namespace, output=None)
        # k(f"delete app aqua-app-server-{app_name_suffix}", namespace=app_resource_namespace, output=None)



def wait_for_rollout(kubernetes_cluster, name, namespace="default"):
    while True:
        try:
            if len(kubernetes_cluster.kubectl(f"get {name}", namespace=namespace)) > 0:
                return kubernetes_cluster.kubectl(f"rollout status {name}", namespace=namespace, output=None)
        except Exception as e:
            # FIXME following message is probably on stderr
            # Error from server (NotFound): deployments.apps "aqua-app-server-eaofv-console" not found
            if not repr(e).startswith("Error from server (NotFound)"):
                LOGGER.error(repr(e))
        time.sleep(5)


def app_template(name, name_in_catalog, catalog, version, namespace, values_for_configmap=None, 
                 values_for_secret=None, app_resource_namespace=None):

    app_name = name
    app_version = version
    app_destination_namespace = namespace

    if not app_resource_namespace:
        app_resource_namespace = namespace

    app_manifest = yaml.safe_load(dedent(f"""
      apiVersion: application.giantswarm.io/v1alpha1
      kind: App
      metadata:
        labels:
          app-operator.giantswarm.io/version: 0.0.0
        name: {app_name}
        namespace: {app_resource_namespace}
      spec:
        catalog: {catalog}
        name: {name_in_catalog}
        namespace: {app_destination_namespace}
        version: {app_version}
        # userConfig:
        #   configMap:
        #     name: {app_name}-userconfig
        #     namespace: {app_resource_namespace}
        #   secret:
        #     name: {app_name}-usersecret
        #     namespace: {app_resource_namespace}
        kubeConfig:
          inCluster: true
    """))

    if values_for_configmap:
        app_manifest["spec"]["userConfig"] = {}
        app_manifest["spec"]["userConfig"]["configMap"] = {
            "name": f"{app_name}-userconfig",
            "namespace": f"{app_resource_namespace}"
        }

        app_configmap_manifest = yaml.safe_load(dedent(f"""
            apiVersion: v1
            kind: ConfigMap
            metadata:
              name: {app_name}-userconfig
              namespace: {app_resource_namespace}
            data:
              values: |
{indent(yaml.safe_dump(values_for_configmap, width=None), '                ')}
        """))

        # app_configmap_manifest["data"]["values"] = yaml.safe_dump(values_for_configmap)

    # if values_as_secret:
    #     # app_manifest["spec"]["userConfig"] = {}
    #     app_manifest["spec"]["userConfig"]["secret"] = {
    #         "name": f"{app_name}-usersecret",
    #         "namespace": f"{app_resource_namespace}"
    #     }

    return [app_manifest, app_configmap_manifest]
