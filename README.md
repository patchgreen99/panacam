# panacam

### Cloud Build
`gcloud builds submit --config app.yaml .`

### Test Build Locally
`docker run gcr.io/handy-contact-219622/panacam`

### Deploy Code
`gcloud container clusters create test-cluster         --num-nodes 1         --scopes https://www.googleapis.com/auth/devstorage.full_control`

`kubectl run hello-server --image gcr.io/handy-contact-219622/panacam --timeout 80000`

### Delete Code
`gcloud container clusters delete test-cluster`