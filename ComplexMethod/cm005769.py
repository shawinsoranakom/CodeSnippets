async def process_events():
            nonlocal count, lines, first_event_seen, end_event_seen
            async for line in response.aiter_lines():
                # Skip empty lines (ndjson uses double newlines)
                if not line:
                    continue

                lines.append(line)
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    logger.debug(f"ERROR: Failed to parse JSON: {line}")
                    raise

                if "job_id" in parsed:
                    assert parsed["job_id"] == job_id
                    continue

                # First event should be vertices_sorted
                if not first_event_seen:
                    assert parsed["event"] == "vertices_sorted", (
                        "Invalid first event. Expected 'vertices_sorted'. Full event stream:\n" + "\n".join(lines)
                    )
                    ids = parsed["data"]["ids"]

                    assert ids == ["ChatInput-vsgM1"], "Invalid ids in first event. Full event stream:\n" + "\n".join(
                        lines
                    )

                    to_run = parsed["data"]["to_run"]
                    expected_to_run = [
                        "ChatInput-vsgM1",
                        "Prompt-VSSGR",
                        "TypeConverterComponent-koSIz",
                        "Memory-8X8Cq",
                        "ChatOutput-NAw0P",
                    ]
                    assert set(to_run) == set(expected_to_run), (
                        "Invalid to_run list in the first event. Full event stream:\n" + "\n".join(lines)
                    )
                    first_event_seen = True
                # Last event should be end
                elif parsed["event"] == "end":
                    end_event_seen = True
                # Middle events should be end_vertex
                elif parsed["event"] == "end_vertex":
                    assert parsed["data"]["build_data"] is not None, (
                        f"Missing build_data at position {count}. Full event stream:\n" + "\n".join(lines)
                    )
                # Other event types (like token or add_message) are allowed and ignored
                else:
                    # Allow other event types to pass through without failing
                    pass

                count += 1

                # Debug output for verbose mode to track progress
                if count % 10 == 0:
                    logger.debug(f"Processed {count} events so far")