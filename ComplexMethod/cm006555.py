async def process_events():
            nonlocal vertices_sorted_seen, end_event_seen, vertex_count

            async for line in response.aiter_lines():
                if not line:
                    continue

                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    errors.append(f"{filename}: Invalid JSON in event stream: {line}")
                    continue

                # Verify job_id in events
                if "job_id" in parsed and parsed["job_id"] != job_id:
                    errors.append(f"{filename}: Job ID mismatch in event stream")
                    continue

                event_type = parsed.get("event")

                if event_type == "vertices_sorted":
                    vertices_sorted_seen = True
                    if not parsed.get("data", {}).get("ids"):
                        errors.append(f"{filename}: Missing vertex IDs in vertices_sorted event")

                elif event_type == "end_vertex":
                    vertex_count += 1
                    if not parsed.get("data", {}).get("build_data"):
                        errors.append(f"{filename}: Missing build_data in end_vertex event")

                elif event_type == "end":
                    end_event_seen = True

                elif event_type == "error":
                    error_data = parsed.get("data", {})
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("error", "Unknown error")
                        # Skip if error is just "False" which is not a real error
                        if error_msg != "False" and error_msg is not False:
                            errors.append(f"{filename}: Flow execution error: {error_msg}")
                    else:
                        error_msg = str(error_data)
                        if error_msg != "False":
                            errors.append(f"{filename}: Flow execution error: {error_msg}")

                elif event_type == "message":
                    # Handle message events (normal part of flow execution)
                    pass

                elif event_type in ["token", "add_message", "stream_closed"]:
                    # Handle other common event types that don't indicate errors
                    pass