# awslambda-otel-sample

## Lambda OpenTelemetry java auto-instrumentation Sample
under `sample-apps/java-lambda` 

Make sure you have aws lambda extensions api trial permission, config aws credencial and aws region as us-east-1
1. run `1-create-bucket.sh`
2. run `2-deploy.sh`
3. run `3-invoke.sh`

Then you can get traces in X-Ray Console.

This sample depends on 2 Lambda layers: aws-otel-auto-instrumentation and otel-collector, now opentelemetry collector config is hardcode as below, will change to be configurable when Lambda Extensions API supports getting environment variable by primitive `os.getEnv()` in next week.
```yaml
extensions:
  health_check:

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:55680

exporters:
  logging:
    loglevel: debug
  awsxray:
    local_mode: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [logging, awsxray]
    metrics:
      receivers: [otlp]
      exporters: [logging]
  extensions: [health_check]
```

By default OTel auto instrumentation uses SpanBatchProcessor, batching timer is 5 seconds. You will see X-Ray segments delay caused by Lambda freeze.
Changing otel.bsp.schedule.delay to 0 will mitigate the delay.

## Build and publish AOC extension Lambda layers
under `extensions/aoc-extension`, run
```shell script
make publish-layer
```

## Build and publish OpenTelemetry java auto-instrumentation Lambda layers
under `extensions/otel-java-extension`, run
```shell script
./publish-layer.sh
```

#### To public your Lambda layer, run:
```shell script
aws lambda add-layer-version-permission --layer-name <your-lambda-layer-name> --version-number <version-number> \                                             ✔  12:51:19 
--principal "*" --statement-id publish --action lambda:GetLayerVersion
```
