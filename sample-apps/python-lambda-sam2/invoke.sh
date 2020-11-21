#!/bin/bash
set -eo pipefail

stack='aot-py38-sample-layer'
region='us-west-1'
APIID=$(aws cloudformation describe-stack-resource --stack-name $stack --region $region --logical-resource-id api --query 'StackResourceDetail.PhysicalResourceId' --output text)

for i in {1..1000}
    do
        echo $i
        curl https://$APIID.execute-api.$region.amazonaws.com/api/ -v
    done
