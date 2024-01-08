# Group6 
## AILoan

### Description

The loan prediction system tackles the difficulties encountered by many financial institutions in efficiently evaluating and assessing a large amount of loan applications. Conventional approaches often involve time-consuming manual assessments which lead to a large backlog of pending applications causing delays and occasional bias, resulting in inconsistent decisions.

Our solution to this problem is to improve the process by using artificial intelligence. This involves using AI to predict the likelihood of loan approval based on previous customer behaviour and historical data.

### Setup Instructions

#### Step 1: clone the project
Via SSH run 

`git clone git@git.chalmers.se:courses/dit826/2023/group6/ailoan.git`

Via HTTPS run 

`git clone https://git.chalmers.se/courses/dit826/2023/group6/ailoan.git`

#### Step 2: Install django and libraries
Navigate to `cd ailoan/loanProject/`

Run the requirements file `pip install -r requirements.txt`

#### Step 3: Run the project
Run the project `python manage.py runserver`

### Containerise and push the project using docker
Inside the same directory, run the Dockerfile

`docker login registry.git.chalmers.se`

`docker build -t registry.git.chalmers.se/courses/dit826/2023/group6/ailoan .`

`docker run -p 8000:8000 registry.git.chalmers.se/courses/dit826/2023/group6/ailoan` 

`docker push registry.git.chalmers.se/courses/dit826/2023/group6/ailoan`

### Run and deploy on Kubernetes
Prerequisites
1. Kubernetes
2. Minikube
3. Docker

Start Minikube

`minikube start`

Create a pod

`kubectl apply -f pod.yaml`

Create a service

`kubectl apply -f loanappsvc.yaml`

Deploy

`kubectl apply -f loan.yaml`

### Tools and Techology
* Djangos
* Pandas
* Tensorflow
* scikit-learn
* Dockers and Kubernetes
* SQLlite

### Contributors
* Akuen Akoi Deng
* Cynthia Tarwireyi
* Daniel Dovhun
* Kanokwan Haesatith
* Nazli Moghaddam


