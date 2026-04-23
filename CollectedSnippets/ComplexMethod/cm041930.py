async def stream(self) -> dict:
        if isinstance(self._event_source, bytes):
            raise RuntimeError(
                f"Request failed, msg: {self._event_source.decode('utf-8')}, please ref to `https://open.bigmodel.cn/dev/api#error-code-v3`"
            )
        async for chunk in self._event_source:
            line = chunk.data.decode("utf-8")
            if line.startswith(":") or not line:
                return

            field, _p, value = line.partition(":")
            if value.startswith(" "):
                value = value[1:]
            if field == "data":
                if value.startswith("[DONE]"):
                    break
                data = json.loads(value)
                yield data