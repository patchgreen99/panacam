# panacam

### Cloud Build
`gcloud builds submit --config=app.yaml --timeout 80000` 

### Test Locally
`docker build -t panacam . && docker run -p 8000:8000 -e url=bondicamera panacam`


### Deploy Code
`gcloud container clusters create test-cluster         --num-nodes 3         --scopes https://www.googleapis.com/auth/devstorage.full_control`

`kubectl run server-bondicamera --env="CAMNAME=bondicamera" --image gcr.io/handy-contact-219622/panacam`
`kubectl run server-maroubracamera --env="CAMNAME=maroubracamera" --image gcr.io/handy-contact-219622/panacam`
`kubectl run server-manlycamerahd --env="CAMNAME=manlycamerahd" --image gcr.io/handy-contact-219622/panacam`


### Delete Code
`gcloud container clusters delete test-cluster`


