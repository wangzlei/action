print('hello world!')

import pytest
import os

pathlist = ['aws_observability/aws_observability_sdk', '/usr/local/bin']
os.environ['PATH'] = os.pathsep + os.pathsep.join(pathlist)
os.environ['_HANDLER'] = 'lambda.handler'

def test_auto_instrumentation(capsys):
    os.system("aws_observability/aws_observability_sdk/aot-instrument \
        python3 \
        aws_observability/tests/test_aws_observability.py")
