async def _flush_to_database(self, error: Exception | None = None) -> None:
        """Persist the completed trace and all its spans in a single DB session to minimise round-trips."""
        try:
            from lfx.services.deps import session_scope

            from langflow.services.database.models.traces.model import SpanTable, TraceTable

            try:
                flow_uuid = UUID(self.flow_id)
            except (ValueError, TypeError):
                # Deterministic fallback so malformed flow_ids don't silently discard trace data.
                flow_uuid = uuid5(LANGFLOW_SPAN_NAMESPACE, f"invalid-flow-id:{self.flow_id}")
                logger.error(
                    "Invalid flow_id format — trace will be persisted with a sentinel flow_id. "
                    "flow_id=%r trace_id=%s sentinel_flow_id=%s",
                    self.flow_id,
                    self.trace_id,
                    flow_uuid,
                )

            end_time = datetime.now(tz=timezone.utc)
            total_latency_ms = int((end_time - self._start_time).total_seconds() * 1000)

            # Propagate any child span error to the trace so the UI can filter by status.
            has_span_errors = any(span.get("status") == SpanStatus.ERROR for span in self.completed_spans)
            trace_status = SpanStatus.ERROR if (error or has_span_errors) else SpanStatus.OK

            # Only sum LangChain spans because component spans already aggregate their children's
            # tokens — summing both levels would double-count every LLM call.
            # OTel spec requires deriving total from input+output (no standard total_tokens key)
            from langflow.services.tracing.formatting import safe_int_tokens

            total_tokens = sum(
                safe_int_tokens((span.get("attributes") or {}).get("gen_ai.usage.input_tokens"))
                + safe_int_tokens((span.get("attributes") or {}).get("gen_ai.usage.output_tokens"))
                for span in self.completed_spans
                if span.get("span_source") == "langchain"
            )

            async with session_scope() as session:
                trace = TraceTable(
                    id=self.trace_id,
                    name=self.trace_name,
                    flow_id=flow_uuid,
                    session_id=self.session_id,
                    status=trace_status,
                    start_time=self._start_time,
                    end_time=end_time,
                    total_latency_ms=total_latency_ms,
                    total_tokens=total_tokens,
                )
                await session.merge(trace)

                # Pre-compute UUIDs and topologically sort so parents are inserted
                # before children — required by PostgreSQL's immediate FK enforcement
                # on span.parent_span_id → span.id.
                resolved = resolve_span_uuids(self.completed_spans, self.trace_id)
                resolved = topological_sort_spans(resolved)

                for span_data, span_uuid, parent_uuid in resolved:
                    span = SpanTable(
                        id=span_uuid,
                        trace_id=self.trace_id,
                        parent_span_id=parent_uuid,
                        name=span_data["name"],
                        span_type=span_data["span_type"],
                        status=span_data["status"],
                        start_time=span_data["start_time"],
                        end_time=span_data["end_time"],
                        latency_ms=span_data["latency_ms"],
                        inputs=span_data["inputs"],
                        outputs=span_data["outputs"],
                        error=span_data.get("error"),
                        attributes=span_data.get("attributes") or {},
                    )
                    await session.merge(span)

                logger.debug("Flushed %d spans to database", len(self.completed_spans))

        except Exception:
            logger.exception("Error flushing trace data to database")
            raise