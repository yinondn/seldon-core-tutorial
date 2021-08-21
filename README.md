# seldon-core-on-aws-quickstart-tutorial

This tutorial shows to run ML model serving at scale on AWS using Seldon Core.

## Pre-Requisits
### Kuberenetes cluster
To install Seldon Core you'll need a Kubernetes cluster version equal or higher than 1.12.

Follow the latest [AWS EKS docs](https://docs.aws.amazon.com/eks/latest/userguide/create-cluster.html) to find the setup option that best suits your needs.

Below is an example of how to create EKS cluster using `eksctl`:
1. [Install eksctl](https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html).
2. Run in terminal:
    ```bash
    eksctl create cluster \
    --name eks-model-serving \
    --version 1.21 \
    --region us-east-2 \
    --nodegroup-name linux-nodes \
    --node-type t3.medium \
    --nodes 1 \
    --nodes-min 1 \
    --nodes-max 1 \
    --managed
    ```
3. [Install kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl).
    
    For example, to install on macOS using Homebrew:
    ```bash
    brew install kubectl
    ```
4. [Install AWS CLI version 2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html).
6. [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)
7. Configure kubectl:
   ```bash
   aws eks --region us-east-2 update-kubeconfig --name eks-model-serving
   ```
8. Verify kubectl is properly configured:
   ```bash
   kubectl cluster-info
   ```
### Helm
You'll need Helm version equal or higher than 3.0.

Follow the latest [Helm docs](https://helm.sh/docs/intro/install/) to find the setup option that best suits your needs.

For example, to install helm with Homebew on macOS run:
```bash
brew install helm
```

### Ingress
In order to route traffic to your models you will need to install Ingress. Seldon Core supports Istio or Ambassador. In this tutorial we will use Ambassador.

Follow the latest [Ambassador docs](https://www.getambassador.io/docs/edge-stack/latest/topics/install/) to find the setup option that best suits your needs.

For example, to install via helm 3 run:
```bash
helm repo add datawire https://www.getambassador.io
kubectl create namespace ambassador
helm install ambassador --namespace ambassador datawire/ambassador
```
Finish the installation by running the following command: edgectl install. [Edge Control](https://www.getambassador.io/docs/edge-stack/latest/topics/using/edgectl/edge-control) (edgectl) automatically configures TLS for your instance and provisions a domain name for your Ambassador Edge Stack. This is not necessary if you already have a domain name and certificates.  (optional)
```bash
edgectl install
```

Finally get the IP of the load balancer ambassador just created - you will use it later to send requests to your models:
```bash
export LOAD_BALANCER_IP=$(kubectl get svc --namespace ambassador ambassador -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo $LOAD_BALANCER_IP
```

## Installing Seldon Core
Follow the latest [Seldon install docs](https://docs.seldon.io/projects/seldon-core/en/latest/workflow/install.html).

For example, to install via helm 3 run:
```bash
kubectl create namespace seldon-system
helm install seldon-core seldon-core-operator \
    --repo https://storage.googleapis.com/seldon-charts \
    --set usageMetrics.enabled=true \
    --namespace seldon-system \
    --set ambassador.enabled=true
```

## Deploying a model using a pre-packaged inference server
1. Create a namespace for your models:
    ```bash
    kubectl create namespace my-models
    ```
2. Apply a SeldonDeployment to deploy your model:
```bash
kubectl apply -f - << END
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: iris-model
  namespace: my-models
spec:
  name: iris
  predictors:
  - graph:
      implementation: SKLEARN_SERVER
      modelUri: gs://seldon-models/v1.10.0-dev/sklearn/iris
      name: classifier
    name: default
    replicas: 1
END
```
3. Check deployment status. You should get `"state": "Available"`:
    ```bash
    kubectl get sdep iris-model -o json --namespace my-models | jq .status
    ```
4. Now access the OpenAPI UI of your deployed model: `http://<ingress_url>/seldon/<namespace>/<model-name>/api/v1.0/doc/`
   
   Which in our example resolves to:
   ```bash
   echo https://$LOAD_BALANCER_IP/seldon/my-models/iris-model/api/v1.0/doc/
   ```

    You can use the OpenAPI UI to send requests to your model and get prediction results. Try it out with this data:
    ```json
    { "data": { "ndarray": [[1,2,3,4]] } }
    ```

    Alternatively you can use any other client, for example `curl` or `Postman`, as well as [Seldon Python Client](https://docs.seldon.io/projects/seldon-core/en/latest/python/seldon_client.html):
    ```bash
    curl -X POST https://<ingress>/seldon/seldon/iris-model/api/v1.0/predictions \
    -H 'Content-Type: application/json' \
    -d '{ "data": { "ndarray": [[1,2,3,4]] } }'
    ```
    Note: If you haven't set up a SSL certificate properly (which we won't in the scope of this tutorial), you will need to ignore SSL errors in your clients. For example in curl add `-k` argument.
