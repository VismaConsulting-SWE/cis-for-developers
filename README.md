# CIS in Docker

## Description  
This project enables you to edit and run CIS Python components in your IDE and also deploy them to your CIS Docker Container.  

## How to install CIS  

1) Install this project by:
* Download as zip and unzip 
* or
* Clone repo to your computer
2) Open folder 'docker-compose' and run 'docker-compose up -d' to start the containers.
```shell
cd docker-compose
docker-compose up -d
```

## Editing *deploy_to_docker_cis.py*

Change variable:  
*target_folder = r"C:\CISWork\Docker\integration-services\docker-compose\server-data\workspace\internal\default\component"*  
to point to your Docker Installation *component* folder.

## Python version

Best practise is to use Python 3.* shipped with the CIS-server package, but it works with an already installed Python 3.*  

### To use CIS Python 3.*

Download [Windows CIS-server package](http://www.siriusit.net/ciceron/is/v27/cis-2.7.7.0-3-1-20210420-1601.zip) and extract Python3 folder from ZIP. Set your Python interpreter in IDE to use CIS-Python.

## This mini project

When CIS Docker container is up and running.

### Try CIS-mock in your IDE

- Start/execute the python component *template_for_cis.py* in your IDE.  
Check output in console.  


- Start/execute the integration from within CIS container using URL:
  <http://localhost:10001/integration?wid=internal%3Adefault%2Fdefault&name=cis%20docker>    
  If userid/password is needed, use: support/support  
  Check output result in event log: *Name: Empty / Film: No data sent in body/payload*    


- Use this URL to send data from web browser  
  <http://localhost:10100/rest/start/sync/integration/cis%20docker.if?wid=internal:default/default&surname=Kenobi&givenname=Obi-Wan>  
  Check output in event log  


- Use same URL to send payload/body data from POSTMAN or similar.

  Import and use the file *utils/CIS Docker.postman_collection.json* in POSTMAN  
  Check output in event log
  
### Edit and deploy *template_for_cis.py*

Do some changes to the file and use *deploy_to_docker_cis.py* to deploy it.

### Create components based on *template_for_cis.py*

Add your own components based on the template and add the filename to this list in *deploy_to_docker.py*  
`files_to_deploy = [
    (source_folder, target_folder, 'template_for_cis.py'),  
    (source_folder, target_folder, 'my_own.py')
]`

When component is created, tested and deployed. Create new integration and add that component to the integration. (You can also add the component to any existing integration.)  

Create a new integration in CIS using this URL:  
<http://localhost:10001/new_task_item?wid=internal%3Adefault%2Fdefault>  
