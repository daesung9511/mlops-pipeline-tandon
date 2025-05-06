This directory configures MinIO to the production endpoint.

# Directions
First, create a shared network, so that future services defined in other Docker compose files will also be able to access these services using container names.
```
# runs on node-eval-loop
docker network create production_net
```

Then, bring up the services:
```
# runs on node-eval-loop
docker compose -f eval-loop-chi/docker/docker-compose-production.yaml up -d
```

Open the MinIO object store web UI - in a browser, open
http://A.B.C.D:9001