# python-kubeless

This tutorial will show you how to use Okteto to develop your `kubeless` functions directly in your Kubernetes cluster.

# Install Kubeless in your Kubernetes cluster

First, you need to install `kubeless`. Full instructions [are available here](https://kubeless.io/docs).

`kubeless` contains two pieces: a controller that's running on your Kubernetes cluster, and a CLI that runs on your development machine.

Run the commands below to install Kubeless in your cluster:

```console
export RELEASE=$(curl -s https://api.github.com/repos/kubeless/kubeless/releases/latest | grep tag_name | cut -d '"' -f 4)
$ kubectl create ns kubeless
$ kubectl create -f https://github.com/kubeless/kubeless/releases/download/$RELEASE/kubeless-$RELEASE.yaml
```

```
clusterrole.rbac.authorization.k8s.io/kubeless-controller-deployer created
clusterrolebinding.rbac.authorization.k8s.io/kubeless-controller-deployer created
customresourcedefinition.apiextensions.k8s.io/functions.kubeless.io created
customresourcedefinition.apiextensions.k8s.io/httptriggers.kubeless.io created
customresourcedefinition.apiextensions.k8s.io/cronjobtriggers.kubeless.io created
configmap/kubeless-config created
deployment.apps/kubeless-controller-manager created
serviceaccount/controller-acct created
````

This will install Kubeless' CRDS as well as create a deployment with the controller. You can check the status of the deployment by running the command below:

```console
$ kubectl get pod -n=kubeless
```

```
NAME                                           READY   STATUS    RESTARTS   AGE
kubeless-controller-manager-7ccdccb78b-hn7mf   3/3     Running   0          1m
```

For installing `kubeless` CLI using execute:

## Linux / MacOS

```console
export OS=$(uname -s| tr '[:upper:]' '[:lower:]')
curl -OL https://github.com/kubeless/kubeless/releases/download/$RELEASE/kubeless_$OS-amd64.zip && \
  unzip kubeless_$OS-amd64.zip && \
  sudo mv bundles/kubeless_$OS-amd64/kubeless /usr/local/bin/
```

## Windows

1. Download the latest release from the releases page.
1. Extract the content and add the kubeless binary to the system PATH.

# Deploy your first Kubeless function

We are now ready to create a function. We'll keep it simply and create a function that simply says hello and echos data back. 

Open your favorite IDE, create a file named `hello.py` and past the code below:

```python
def hello(event, context):
  print event
  return 'Hello, you said: %s' % event['data']
```

Functions in Kubeless have the same format regardless of the language of the function or the event source. In general, every function:

1. Receives an object event as their first parameter. This parameter includes all the information regarding the event source. In particular, the key 'data' should contain the body of the function request.
1. Receives a second object context with general information about the function.
1. Returns a string/object that will be used as response for the caller.

More information on functions [is available here](https://kubeless.io/docs/kubeless-functions#functions-interface).

Create the function with the `kubeless` CLI:

```console
$ kubeless function deploy hello --runtime python2.7 --from-file hello.py --handler hello.hello
```

```console
INFO[0000] Deploying function...
INFO[0000] Function hello submitted for deployment
INFO[0000] Check the deployment status executing 'kubeless function ls hello'
```

Let's take a closer look at the command:

1. hello: This is the name of the function we want to deploy.
1.  --runtime python2.7: This is the runtime we want to use to run our function. Run kubeless get-server-config to see all the available options.
1. --from-file function.py: This is the file containing the function code. This can be a file or a zip file of up to 1MB of size.
1. --handler function.hello: This specifies the file and the exposed function that will be used when receiving requests. 

Your function will be ready in a minute or so. Check its state by running the command below:

```console
$ kubeless function ls
```

```
NAME 	NAMESPACE	HANDLER    	RUNTIME  	DEPENDENCIES	STATUS
hello	default   hello.hello	python2.7	            	1/1 READY
```

Once the function is ready, you can call it by running:

```console
$ kubeless function call hello --data 'Hey'
```

```
Hello, you said: Hey
```

# Develop your Function directly in Kubernetes with Okteto.

If you look into your cluster after deploying your function, you'll notice that the `kubeless` controller created (among several things) a deployment to run your function code. This means that you can use `okteto` to develop it directly in the cluster!

`okteto` provides a local development experience for Kubernetes applications. You code locally in your favorite IDE and Okteto synchronizes it automatically to your cluster. The Okteto CLI is open source, and the code is [on Github](https://github.com/okteto/okteto). It is a client-side only tool that works in any Kubernetes cluster.

Follow the [instructions available here](https://okteto.com/docs/getting-started/installation) to install `okteto`.

The first thing we need to do is generate the `okteto` manifest. The manifest tells `okteto` which deployment you are going to be working on and where to synchronize your code. Go back to your favorite IDE, create a file named `okteto.yml`, and paste the content below:

```yaml
name: hello
command:
- bash
workdir: /
mountpath: /kubeless
```

Let's take a deeper look the content of the manifest:

1. name: This is the name of the function you want to develop in.
1. command: This is the command you want to execute. We use `bash` to get a remote terminal into our development container.
1. workdir: This is the working directory of our remote terminal. We use  `/` because that's where we are going to be executing our code from.
1. mountpath: Our local files will be synchronized to this path.


You are ready to start developing in the cluster. Go back to your terminal and run the command below:
```
$ okteto up
```

```
 ✓  Development container activated
 ✓  Files synchronized
    Namespace: okteto
    Name:      hello

I have no name!@hello-8497c7694f-lgd98:/$
```

The command will "drop us" in a terminal inside our development container. This is the same container that `kubeless` uses for your function, except that `okteto` is keeping your file system automatically synchronized.

To start your function, simply run the command below. This is the same command that `kubeless` runs to star the function:

```console
$ python2.7 kubeless.py
```

```console
Bottle v0.12.13 server starting up (using CherryPyServer())...
Listening on http://0.0.0.0:8080/
Hit Ctrl-C to quit.
```

At this point, your function is up and running, just as if you deployed it with `kubeless`. Open a second local terminal, and call it using the `kubeless` CLI:

```console
$ kubeless function call hello --data 'Hey'
```

```
Hello, you said: Hey
```

Now it's time to see some magic. Open `hello.py` in your favorite IDE, change the response message and save the file:

```python
def hello(event, context):
  print event
  return 'Hello from Okteto, you said: %s' % event['data']
```

Go back to the remote terminal, press `CTRL+C` to stop your function, and then start it again.

```console
$ python2.7 kubeless.py
```

```console
Bottle v0.12.13 server starting up (using CherryPyServer())...
Listening on http://0.0.0.0:8080/
Hit Ctrl-C to quit.
```

Call your function again from the second terminal:

```console
$ kubeless function call hello --data 'Hey'
```

```
Hello Kubernetes, you said: Hey
```

Look at that response carefully. Notice something different? Your code changes were applied instantly, without you having to redeploy your function. Pretty cool no?

## How does it work?

When you run `python2.7 kubeless.py`, the kubeless script dynamically loads the contents of the `/kubeless` folder, and then uses it to execute your function when it gets a request. Behind the scenes, `okteto` is keeping your local folder synchronized with the `/kubeless` folder. Everytime you create, save, or delete a file, the change is automatically replicated in your function's container.  

This file synchronizing is what allows you to quickly iterate in your changes, without having to redeploy your function every time. 

More information on this [is available here](https://github.com/okteto/okteto#how-it-works).

# Conclusion

In this tutorial we show you how to use `okteto` together with `kubeless` to speed up your development cycle. Traditionally, you'd have to write your code locally, package it and deploy it to Kubernetes in order to test your changes. 

With `okteto`, you run `okteto up` once, and iterate directly in your function's container. Not only do you have minutes on each validation loop, but since you are running your code directly in your container, you are also testing that your code works as a `kubeless` function from the very beginning.

`okteto` works with pretty much any Cloud Native Application. Check out our samples repository to learn how to use `okteto` with your favorite framework and programming language.

# Cleanup

You can delete the function using the command below:

```console
$ kubeless function delete hello
$ kubeless function ls
```

```
NAME        NAMESPACE   HANDLER     RUNTIME     DEPENDENCIES    STATUS
```

And to delete `kubeless`:

```
$ kubectl delete -f https://github.com/kubeless/kubeless/releases/download/$RELEASE/kubeless-$RELEASE.yaml
```