#!/bin/bash
TEMPLATE=template.yml
CONFIG=samconfig.toml
# TEMPLATE=template-py37.yml
# CONFIG=samconfig-py37.toml
rm -rf .aws-sam
rm -rf aws_observability_collector
mkdir aws_observability_collector && cp -r ../../extensions/aoc-extension/* aws_observability_collector
# remove local cp if aoc lambda is ready
# cp /Users/wangzl/workspace/aws-ob/aws-otel-collector/build/linux/aoc_linux_x86_64 aws_observability_collector
wget -O aws_observability_collector/aoc_linux_x86_64 https://github.com/open-telemetry/opentelemetry-collector-contrib/releases/download/v0.14.0/otelcontribcol_linux_amd64
sam build -u -t $TEMPLATE
find .aws-sam -name __pycache__ -exec rm -rf  {} \;
sam deploy --stack-name aot-py38-sample-layer --capabilities CAPABILITY_NAMED_IAM --resolve-s3 --region us-west-2
# sam deploy -g
