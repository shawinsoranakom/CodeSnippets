async def parse_sse_stream(stream: aiohttp.StreamReader) -> AsyncGenerator[Dict[str, Any], None]:
            """Parse SSE stream yielding parsed JSON objects"""
            buffer = ""
            object_buffer = ""

            async for chunk_bytes in stream.iter_any():
                chunk = chunk_bytes.decode()
                buffer += chunk
                lines = buffer.split("\n")
                buffer = lines.pop()  # Save last incomplete line back

                for line in lines:
                    line = line.strip()
                    if line == "":
                        # Empty line indicates end of SSE message -> parse object buffer
                        if object_buffer:
                            try:
                                yield json.loads(object_buffer)
                            except Exception as e:
                                debug.error(f"Error parsing SSE JSON: {e}")
                            object_buffer = ""
                    elif line.startswith("data: "):
                        object_buffer += line[6:]

            # Final parse when stream ends
            if object_buffer:
                try:
                    yield json.loads(object_buffer)
                except Exception as e:
                    debug.error(f"Error parsing final SSE JSON: {e}")