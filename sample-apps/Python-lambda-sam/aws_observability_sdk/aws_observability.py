import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from opentelemetry import trace

# TODO: aws propagator
from opentelemetry.instrumentation.aws_lambda.tmp.propagator.xray_id_generator import (
    AWSXRayIdsGenerator,
)

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

# resource looks weird because get_aggregated_resources has bug, cannot merge _DEFAULT otel attributes
resource = Resource.create().merge(AwsLambdaResourceDetector().detect())
trace.set_tracer_provider(
    TracerProvider(
        ids_generator=AWSXRayIdsGenerator(),
        resource=resource,
    )
)

trace.get_tracer_provider().add_span_processor(
    SimpleExportSpanProcessor(ConsoleSpanExporter())
)

in_process = os.environ.get("INPROCESS_EXPORTER", None)
if in_process is None or in_process.lower() != "true":
    from opentelemetry.exporter.otlp.trace_exporter import OTLPSpanExporter
    # otlp_exporter = OTLPSpanExporter(endpoint="localhost:55680")
    otlp_exporter = OTLPSpanExporter(endpoint="localhost:55680", insecure=True)
    span_processor = BatchExportSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    logger.info("OTLP exporter is ready ...")
else:
    from opentelemetry.exporter.xray import XraySpanExporter

    xraySpanExporter = XraySpanExporter()
    trace.get_tracer_provider().add_span_processor(
        BatchExportSpanProcessor(xraySpanExporter)
    )
    logger.info("AWS Xray in-process exporter is ready ...")

from importlib import import_module

from opentelemetry.instrumentation.aws_lambda import AwsLambdaInstrumentor
AwsLambdaInstrumentor().instrument()

# Load instrumentors from entry_points
from pkg_resources import iter_entry_points
for entry_point in iter_entry_points("opentelemetry_instrumentor"):
    print(entry_point)
    try:
        entry_point.load()().instrument()  # type: ignore
        logger.info("Instrumented %s", entry_point.name)

    except Exception:
        logger.exception("Instrumenting of %s failed", entry_point.name)


def modify_module_name(module_name):
    """Returns a valid modified module to get imported"""
    return ".".join(module_name.split("/"))


class HandlerError(Exception):
    pass

path = os.environ.get("ORIG_HANDLER", None)
if path is None:
    raise HandlerError("ORIG_HANDLER is not defined.")
parts = path.rsplit(".", 1)
if len(parts) != 2:
    raise HandlerError("Value %s for ORIG_HANDLER has invalid format." % path)

(mod_name, handler_name) = parts
modified_mod_name = modify_module_name(mod_name)
handler_module = import_module(modified_mod_name)
lambda_handler = getattr(handler_module, handler_name)
