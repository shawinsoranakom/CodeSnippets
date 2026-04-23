def ask(self, question="", stream=False, **kwargs):
        """
        Ask a question to the session. If stream=True, yields Message objects as they arrive (SSE streaming).
        If stream=False, returns a single Message object for the final answer.
        """
        if self.__session_type == "agent":
            res = self._ask_agent(question, stream, **kwargs)
        elif self.__session_type == "chat":
            res = self._ask_chat(question, stream, **kwargs)
        else:
            raise Exception(f"Unknown session type: {self.__session_type}")

        if stream:
            for line in res.iter_lines(decode_unicode=True):
                if not line:
                    continue  # Skip empty lines
                line = line.strip()
                if line.startswith("data:"):
                    content = line[len("data:"):].strip()
                    if content == "[DONE]":
                        break  # End of stream
                else:
                    content = line

                try:
                    json_data = json.loads(content)
                except json.JSONDecodeError:
                    continue  # Skip lines that are not valid JSON

                event = json_data.get("event",None)
                if event and event != "message":
                    continue

                if (
                    (self.__session_type == "agent" and event == "message_end")
                    or (self.__session_type == "chat" and json_data.get("data") is True)
                ):
                    return
                if self.__session_type == "agent":
                    yield self._structure_answer(json_data)
                else:
                    yield self._structure_answer(json_data["data"])
        else:
            try:
                json_data = res.json()
            except ValueError:
                raise Exception(f"Invalid response {res}")
            yield self._structure_answer(json_data["data"])