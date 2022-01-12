# Centralized Storage Resource Tagging API

    This project contains a centralized API to put resource level tags for AWS storage resources to backup/skip backup of the resource by AWS Backup service.
    The following types of resources are currently supported by the API:
    * RDS
    * EFS
    * EBS
    * Dynamodb
    * FSx
    * Redshift

## Architecture
![Architecture2](docs/arch.png)

```
.
├── README.md                           <-- This documentation file
├── storage_resource_tagging            <-- Lambda function that adds schedule tags for a resource
├── storage_resource_exception_tagging  <-- Lambda function that deletes schedule tags for a resource
├── utils                               <-- shared functions
├── config                              <-- configuration params
├── docs                                <-- Swagger doc 
├── Pipfile                             <-- Python dependencies
└── serverless.yml                      <-- Serverless application definition file
```
## Pre-requisites
```shell script
Install NodeJS
Install Serverless framework
Install Python 3.6, Pip3
```


## Test
```shell script
#Install Python requirements
pip3 install -r requirements.txt

pytest ./
```

## Deployment
```shell script
# Install serverless framework dependencies from package.json
npm i

#Deploy API
serverless deploy -s dev
```

## Integration Test
```
behave storage_resource_tagging/tests/bdd/
behave storage_resource_exception_tagging/tests/bdd/
```

## OpenAPI Spec
The OpenAPI spec for the API is located at [docs/swagger.yml](docs/swagger.yml)

## Example Usage

```bash
# Add tag "vpcx-backup:regular" to all RDS instances in account-id=itx-000, in region=us-west-2 

curl -X PUT 
     -H 'Content-Type: application/json' 
     -H 'authorization: Bearer AMvcMSfZoAHnlXX0cAIhAKsJx8Pp' 
     -d {"vpcx-backup": "regular"}, {"cost_center": "12453"}
     https://vpce-01227fc69-kykwwlo6.execute-api.us-east-1.vpce.amazonaws.com/dev/v1/accounts/itx-000/regions/us-west-2/rds/storage/tags


# Add tag "vpcx-skip-backup:true" tag for account-id=itx-000, in region=us-west-2 and for specific resources in the request body

curl -X PUT 
     -H 'Content-Type: application/json' 
     -H 'authorization: Bearer AMvcMSfZoAHnlXX0cAIhAKsJx8Pp' 
    -d  {'ResourceArns':[
            'arn:aws:rds:us-east-1:123456789012:db:rds_db_instance', 
            'arn:aws:redshift:us-east-1:594917905844:namespace/redsfhit-cluster-namespace'
         ], 
        'VolumeIds':[
            'vol-054533f7abcb561bf', 
            'vol-054533f7abcb4533f'
         ]
        }
     https://vpce-012427fc69-kykwwlo6.execute-api.us-east-1.vpce.amazonaws.com/dev/v1/accounts/itx-000/regions/us-west-2/exceptions/backup/enable

```

## License
This library is licensed under the MIT-0 License. See the LICENSE file.