# Testing the charts


```bash
kind create cluster
# or giantswarm tenant

apptestctl bootstrap


# edit the `Chart.yaml`s in helm with the to be tested version
# for example "5.3-gs1"

# push dev version to chartmuseum. delete before if it already exists
# [!] the following works in fish-shell. couldn't figure out the
# bash aquivalent yet for the timeout/sleep trick
set app_version "5.3-gs1"

timeout 10 kubectl -n giantswarm port-forward service/chartmuseum-chartmuseum 8080:8080 & ; sleep 2
for app_name in "aqua-app-server" "aqua-app-scanner" "aqua-app-enforcer"
  helm package ./helm/$app_name
  curl --request DELETE http://localhost:8080/api/charts/$app_name/$app_version
  curl --data-binary "@$app_name-$app_version.tgz" http://localhost:8080/api/charts
  curl -sS http://localhost:8080/api/charts | jq '."'"$app_name"'"[] | {name, version}'
end


# the aqua test needs two files with credentials to be present.
#
# just the licence token in a plain text file
# -> ./tests_proposal/secrets/aqua-license-token
#
# and a pull secret for the quay.io giantswarm account     
# -> ./tests_proposal/secrets/registry-auth-quay-secret.yaml
# should look like this:
#
# kind: Secret
# apiVersion: v1
# metadata:
#   name: giantswarm-partner-aqua-pull-secret
# type: kubernetes.io/dockerconfigjson
# data:
#   .dockerconfigjson: {}
#
# you can create that file like this:
# $ docker login quay.io/giantswarm
#
# $ docker_config_quay=$(cat $HOME/.docker/config.json \
#   | jq -c '{auths:{"quay.io":.auths."quay.io"}, HttpHeaders}')
#
# $ kubectl create secret generic -n aqua-app giantswarm-partner-aqua-pull-secret \
#   --from-literal=.dockerconfigjson="$docker_config_quay" \
#   --type=kubernetes.io/dockerconfigjson \
#   --dry-run=client -o json


docker build -t local/pytest-kube ./tests_proposal/docker

# example for noisy output and keeping the namespace
# with the deployed chart
docker run -ti \
  -v $PWD/tests_proposal:/pytest \
  -v $KUBECONFIG:/root/.kube/config \
  local/pytest-kube python -m pytest -s \
    -o log_cli=true -o log_cli_level=INFO \
      ./test_install.py --keep-namespace


# simple run with removing the namespace in the end
docker run -ti \
  -v $PWD/tests_proposal:/pytest \
  -v $KUBECONFIG:/root/.kube/config \
  local/pytest-kube python -m pytest
```