from __future__ import absolute_import  # need it??
import os
import logging
import jsonpickle

from opentelemetry import trace
# TODO: aws propagator
from opentelemetry.instrumentation.aws_lambda.tmp.propagator.xray_id_generator import AWSXRayIdsGenerator

from opentelemetry.sdk.resources import (
    Resource,
    OTELResourceDetector,
    get_aggregated_resources,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
    BatchExportSpanProcessor,
)

from opentelemetry.resource import AwsLambdaResourceDetector

logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

# resource looks weird because get_aggregated_resources has bug, cannot merge _DEFAULT otel attributes
resource=Resource.create().merge(AwsLambdaResourceDetector().detect())
trace.set_tracer_provider(TracerProvider(
    ids_generator=AWSXRayIdsGenerator(), 
    resource=resource,)
)

trace.get_tracer_provider().add_span_processor(
    BatchExportSpanProcessor(ConsoleSpanExporter())
)

in_process = os.environ.get("INPROCESS_EXPORTER", None)
if in_process is None or in_process.lower() != 'true':
    # === otlp exporter, collector
    from opentelemetry.exporter.otlp.trace_exporter import OTLPSpanExporter
    # otlp_exporter = OTLPSpanExporter(endpoint="localhost:55680")
    otlp_exporter = OTLPSpanExporter(endpoint="localhost:55680", insecure=True)
    span_processor = BatchExportSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    logger.info("OTLP exporter is ready ...")
else:
    # === xray/xraydaemon exporter
    from opentelemetry.exporter.xray import XraySpanExporter
    xraySpanExporter = XraySpanExporter()
    trace.get_tracer_provider().add_span_processor(
        BatchExportSpanProcessor(xraySpanExporter)
    )
    logger.info("AWS Xray in-process exporter is ready ...")


tracer = trace.get_tracer(__name__)

from importlib import import_module

def modify_module_name(module_name):
    """Returns a valid modified module to get imported
    """
    return ".".join(module_name.split("/"))


class HandlerError(Exception):
    pass


path = os.environ.get("ORIG_HANDLER", None)
if path is None:
    raise HandlerError(
        "ORIG_HANDLER is not defined."
    )
parts = path.rsplit(".", 1)
if len(parts) != 2:
    raise HandlerError("Value %s for ORIG_HANDLER has invalid format." % path)

(mod_name, handler_name) = parts
modified_mod_name = modify_module_name(mod_name)
handler_module = import_module(modified_mod_name)
lambda_handler = getattr(handler_module, handler_name)


# Manual enable otel instrumentation. Can remove them once we package auto-instrumentation into lambda layer.
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
AioHttpClientInstrumentor().instrument()
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
BotocoreInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
from opentelemetry.instrumentation.aws_lambda import AwsLambdaInstrumentor
AwsLambdaInstrumentor().instrument()
