async def create_chat_completion(self, raw_request: Request):
        try:
            request = await raw_request.json()

            # add params to request
            kv_prepare_request = request.copy()
            kv_prepare_request["max_tokens"] = 1
            if "max_completion_tokens" in kv_prepare_request:
                kv_prepare_request["max_completion_tokens"] = 1

            # prefill stage
            prefill_instance = self.schedule(self.prefill_cycler)
            try:
                async for _ in self.forward_request(
                    f"http://{prefill_instance}/v1/chat/completions", kv_prepare_request
                ):
                    continue
            except HTTPException as http_exc:
                self.remove_instance_endpoint("prefill", prefill_instance)
                raise http_exc
            # Perform kv recv and decoding stage
            decode_instance = self.schedule(self.decode_cycler)

            try:
                generator = self.forward_request(
                    "http://" + decode_instance + "/v1/chat/completions", request
                )
            except HTTPException as http_exc:
                self.remove_instance_endpoint("decode", decode_instance)
                raise http_exc
            response = StreamingResponse(content=generator)
            return response
        except Exception:
            exc_info = sys.exc_info()
            error_messages = [str(e) for e in exc_info if e]
            print("Error occurred in disagg proxy server")
            print(error_messages)
            return StreamingResponse(
                content=iter(error_messages), media_type="text/event-stream"
            )