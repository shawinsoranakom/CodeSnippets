async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            total = len(input_data.to) + len(input_data.cc) + len(input_data.bcc)
            if total > 50:
                raise ValueError(
                    f"Max 50 combined recipients across to, cc, and bcc (got {total})"
                )

            params: dict = {"to": input_data.to}
            if input_data.cc:
                params["cc"] = input_data.cc
            if input_data.bcc:
                params["bcc"] = input_data.bcc
            if input_data.subject:
                params["subject"] = input_data.subject
            if input_data.text:
                params["text"] = input_data.text
            if input_data.html:
                params["html"] = input_data.html

            fwd = await self.forward_message(
                credentials,
                input_data.inbox_id,
                input_data.message_id,
                **params,
            )
            result = fwd.model_dump()

            yield "message_id", fwd.message_id
            yield "thread_id", fwd.thread_id or ""
            yield "result", result
        except Exception as e:
            yield "error", str(e)