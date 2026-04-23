def _transform(self, input: Iterator[str | BaseMessage]) -> Iterator[list[str]]:
        buffer = ""
        for chunk in input:
            if isinstance(chunk, BaseMessage):
                # Extract text
                chunk_content = chunk.content
                if not isinstance(chunk_content, str):
                    continue
                buffer += chunk_content
            else:
                # Add current chunk to buffer
                buffer += chunk
            # Parse buffer into a list of parts
            try:
                done_idx = 0
                # Yield only complete parts
                for m in droplastn(self.parse_iter(buffer), 1):
                    done_idx = m.end()
                    yield [m.group(1)]
                buffer = buffer[done_idx:]
            except NotImplementedError:
                parts = self.parse(buffer)
                # Yield only complete parts
                if len(parts) > 1:
                    for part in parts[:-1]:
                        yield [part]
                    buffer = parts[-1]
        # Yield the last part
        for part in self.parse(buffer):
            yield [part]