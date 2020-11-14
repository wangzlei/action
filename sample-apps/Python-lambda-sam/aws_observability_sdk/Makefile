build-AwsObservabilitySdk:
	mkdir -p $(ARTIFACTS_DIR)/python
	pip3 install -r requirements.txt -t $(ARTIFACTS_DIR)/python
	cp -r * $(ARTIFACTS_DIR)/python
	rm -rf $(ARTIFACTS_DIR)/python/boto*
	rm -rf $(ARTIFACTS_DIR)/python/urllib3*
