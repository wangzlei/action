build:
	GOOS=linux GOARCH=amd64 go build -o bin/opentelemetry-lambda-extension *.go

build-AwsObservabilityCollector:
	rpm --rebuilddb
	yum install -y go
	mkdir -p $(ARTIFACTS_DIR)/extensions
	go build -o $(ARTIFACTS_DIR)/extensions/aoc-extension *.go
	mkdir -p $(ARTIFACTS_DIR)/otelcol
	cp config.yaml $(ARTIFACTS_DIR)/otelcol
