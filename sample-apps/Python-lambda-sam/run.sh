#!/bin/bash

set -e
set -u

echo_usage () {
    echo "usage: Deploy AOT Python Lambda layers from scratch"
    echo " -r <aws region>"
    echo " -t <cloudformation template>"
    echo " -b <sam build>"
    echo " -d <sam deploy>"
    echo " -s <stack name>"
}

main () {
    saved_args="$@"
    region='us-west-2'
    stack='aot-py38-sample-layer'
    template='template.yml'
    build=false
    deploy=false

    while getopts "hbdr:t:s:" opt; do
        case "${opt}" in
            h) echo_usage
                exit 0
                ;;
            b) build=true 
                ;;
            d) deploy=true 
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

    if [[ $build == false && $deploy == false ]]; then
        build=true
        deploy=true
    fi

    if [[ $build == true ]]; then
        echo "sam building..."
        rm -rf .aws-sam
        rm -rf aws_observability_collector
        mkdir aws_observability_collector && cp -r ../../extensions/aoc-extension/* aws_observability_collector
        # remove local cp if aoc lambda is ready
        # cp /Users/wangzl/workspace/aws-ob/aws-otel-collector/build/linux/aoc_linux_x86_64 aws_observability_collector
        wget -O aws_observability_collector/aoc_linux_x86_64 https://github.com/open-telemetry/opentelemetry-collector-contrib/releases/download/v0.14.0/otelcontribcol_linux_amd64
        sam build -u -t $template
        find .aws-sam -name __pycache__ -exec rm -rf  {} \;
    fi

    if [[ $deploy == true ]]; then
        echo "sam deploying..."
        sam deploy --stack-name $stack --capabilities CAPABILITY_NAMED_IAM --resolve-s3 --region $region
    fi  

}

main "$@"