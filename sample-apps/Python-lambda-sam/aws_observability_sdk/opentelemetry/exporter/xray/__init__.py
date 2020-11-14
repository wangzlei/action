import logging
from opentelemetry import trace
import opentelemetry.trace as trace_api
import json
from opentelemetry.sdk.trace.export import Span, SpanExporter, SpanExportResult
from opentelemetry.trace import SpanKind
from .emitter import UDPEmitter
import time
import binascii
import os
import random
import datetime
import boto3
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.context import attach, detach, set_value

logger = logging.getLogger(__name__)


class XraySpanExporter(SpanExporter):
    TRACE_ID_VERSION = "1"
    TRACE_ID_DELIMITER = "-"
    TRACE_ID_FIRST_PART_LENGTH = 8

    def __init__(self):
        self._emitter = UDPEmitter()
        self._xray_client = boto3.client("xray")

    # TODO: sampled or not
    def export(self, spans) -> SpanExportResult:
        logger.info("--- XraySpanExporter emitter ---")

        # TODO: merge segments to one request, else batch processor does not make sense
        for span in spans:
            segment = self._translate_to_segment(span)
            if segment == "":
                continue
            entity = json.dumps(segment)

            # emit segment to daemon or xray ...
            # self._emitter.send_entity(entity)
            logger.info(entity)

            # suppress boto3 instumentation
            token = attach(set_value("suppress_instrumentation", True))
            response = self._xray_client.put_trace_segments(
                TraceSegmentDocuments=[
                    entity,
                ]
            )
            detach(token)
            logger.info(response)

        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

    # TODO: polish this part... ...
    # A barebone translator, from span to xray format.
    def _translate_to_segment(self, span):
        segment = {}
        segment["name"] = span.name

        # traceid, id, parent
        otel_trace_id = "{:032x}".format(span.context.trace_id)
        xray_trace_id = (
            self.TRACE_ID_VERSION
            + self.TRACE_ID_DELIMITER
            + otel_trace_id[: self.TRACE_ID_FIRST_PART_LENGTH]
            + self.TRACE_ID_DELIMITER
            + otel_trace_id[self.TRACE_ID_FIRST_PART_LENGTH :]
        )
        id = "{:016x}".format(span.context.span_id)
        segment["trace_id"] = xray_trace_id
        segment["id"] = id

        parent_context = span.parent
        if parent_context:
            parent_id = "{:016x}".format(parent_context.span_id)

            segment["parent_id"] = parent_id
            segment["type"] = "subsegment"

            # TODO: namespace
            _origin = span.attributes._dict.get("aws.origin", "")
            if _origin != "AWS::Lambda:Function":
                segment["namespace"] = "aws"
                # need to add origin in botocore instrumentor
                # if _origin.startswith('AWS::'):
                #     segment['namespace'] = 'aws'
                # else:
                #     segment['namespace'] = 'remote'
        else:
            # actually in Lambda case there is no segment
            segment["type"] = "segment"

        if "aws.origin" in span.attributes._dict:
            segment["origin"] = "AWS::Lambda::Function"

        # no idea what is the best practice Python process time
        segment["start_time"] = span._start_time / 1000000000
        segment["end_time"] = span._end_time / 1000000000

        # xray resources
        segment["aws"] = span.resource._attributes

        # throw everything into metadata
        awsDict = {**(span.attributes._dict), **(span.resource._attributes)}
        segment["metadata"] = awsDict

        return segment
