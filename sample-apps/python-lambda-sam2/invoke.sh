#!/bin/bash
set -eo pipefail

stack='aot-py38-sample-layer'

APIID=$(aws cloudformation describe-stack-resource --stack-name $stack --logical-resource-id api --query 'StackResourceDetail.PhysicalResourceId' --output text)
REGION='us-west-2'

curl https://$APIID.execute-api.$REGION.amazonaws.com/api/ -v
