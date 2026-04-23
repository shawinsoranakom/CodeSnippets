async def run(
        self,
        input_data: Input,
        *,
        credentials: APIKeyCredentials,
        user_id: str,
        graph_id: str,
        graph_exec_id: str,
        **kwargs,
    ) -> BlockOutput:
        try:
            client = self._get_client(credentials)

            if isinstance(input_data.content, Conversation):
                messages = input_data.content.messages
            elif isinstance(input_data.content, Content):
                messages = [{"role": "user", "content": input_data.content.content}]
            else:
                messages = [{"role": "user", "content": str(input_data.content)}]

            params = {
                "user_id": user_id,
                "output_format": "v1.1",
                "metadata": input_data.metadata,
            }

            if input_data.limit_memory_to_run:
                params["run_id"] = graph_exec_id
            if input_data.limit_memory_to_agent:
                params["agent_id"] = graph_id

            # Use the client to add memory
            result = client.add(
                messages,
                **params,
            )

            results = result.get("results", [])
            yield "results", results

            if len(results) > 0:
                for result in results:
                    yield "action", result["event"]
                    yield "memory", result["memory"]
            else:
                yield "action", "NO_CHANGE"

        except Exception as e:
            yield "error", str(e)