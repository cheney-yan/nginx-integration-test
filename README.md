# A tool to execute end-to-end test for nginx

## Description
This is an end-to-end testing tool for your nginx docker image.

Here I assume you have created your customized nginx image with all the configurations in. This tool allows you to run the docker image locally and then test if all the configurations are all right. 
## install 
```
pip install fire requests dnspython pyyaml
```

## Execution

### Hack your domain name
If your nginx is configured for a host, you need to map it to your local host (or where the docker container is listening on)
```
echo '127.0.0.1 you-nginx-domain-name' | sudo tee -a /etc/hosts
```
### Start nginx locally and pipe the output to the test script
```
docker run --rm --name nginx -p 80:80 local/nginx-image | python test.py 
```
This command will run the nginx-image (assume its name is local/nginx-image) and pipe the output to the test script.
test.py also loads test input from test.yaml file, then compare it with the output of the nginx container.
Note this command won't stop nginx automatically when test finishes. You need to manually stop the running docker process.

### More options

- Check test.yaml for how to provide expected input and expected output.
- run `test.py -- --help` for more options.

