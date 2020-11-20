#!/bin/bash

set -e
set -u

echo_usage () {
    echo "usage: Deploy AOT Python Lambda layers from scratch"
    echo " -r <aws region>"
    echo " -t <cloudformation template>"
    echo " -b <sam build>"
    echo " -d <sam deploy>"
    echo " -i <invoke lambda>"
    echo " -s <stack name>"
}

main () {
    saved_args="$@"
    region=$(aws configure get region)
    stack='aot-py38-sample-layer'
    template='template.yml'
    build=false
    deploy=false
    debug=false
    invoke=false

    while getopts "hbdxir:t:s:" opt; do
        case "${opt}" in
            h) echo_usage
                exit 0
                ;;
            b) build=true
                ;;
            x) debug=true
                ;;
            d) deploy=true
                ;;
            i) invoke=true
                ;;
            r) region="${OPTARG}"
                ;;
            t) template="${OPTARG}"
                ;;
            s) stack="${OPTARG}"
                ;;
            \?) echo "Invalid option: -${OPTARG}" >&2
                exit 1
                ;;
            :)  echo "Option -${OPTARG} requires an argument" >&2
                exit 1
                ;;
        esac
    done

    echo "Invoked with: ${saved_args}"

    if [[ $build == false && $deploy == false && $invoke == false ]]; then
        build=true
        deploy=true
        invoke=true
    fi

    if [[ $build == true ]]; then
        echo "sam building..."
        rm -rf .aws-sam
        rm -rf aws_observability/aws_observability_collector
        mkdir -p aws_observability/aws_observability_collector
        cp -r ../../extensions/aoc-inprocess-extension/* aws_observability/aws_observability_collector
        sam build -u -t $template
        # find . -name __pycache__ -exec rm -rf  {} \; &>/dev/null
    fi

    if [[ $debug == true ]]; then
        echo "debug mode, show code in lambda console"
        mkdir -p .aws-sam/build/function/opentelemetry/instrumentation/auto_instrumentation/
        mv .aws-sam/build/AwsObservability/python/opentelemetry/instrumentation/auto_instrumentation/__init__.py .aws-sam/build/function/opentelemetry/instrumentation/auto_instrumentation/
        mv .aws-sam/build/AwsObservability/python/opentelemetry/instrumentation/auto_instrumentation/sitecustomize.py .aws-sam/build/function/opentelemetry/instrumentation/auto_instrumentation/
        cp .aws-sam/build/AwsObservability/python/bin/opentelemetry-instrument .aws-sam/build/function
        mv .aws-sam/build/AwsObservability/python/aws_observability.py .aws-sam/build/function/
        mv .aws-sam/build/AwsObservability/python/opentelemetry/instrumentation/aws_lambda .aws-sam/build/function/opentelemetry/instrumentation/
    fi

    if [[ $deploy == true ]]; then
        echo "sam deploying..."
        sam deploy --stack-name $stack --capabilities CAPABILITY_NAMED_IAM --resolve-s3 --region $region
        rm -rf aws_observability/aws_observability_collector
    fi

    if [[ $invoke == true ]]; then
        APIID=$(aws cloudformation describe-stack-resource --stack-name $stack --logical-resource-id api --query 'StackResourceDetail.PhysicalResourceId' --output text)
        curl https://$APIID.execute-api.$region.amazonaws.com/api/ -v
    fi
}

main "$@"
