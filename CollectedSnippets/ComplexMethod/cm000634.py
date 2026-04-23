async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            total = len(input_data.to) + len(input_data.cc) + len(input_data.bcc)
            if total > 50:
                raise ValueError(
                    f"Max 50 combined recipients across to, cc, and bcc (got {total})"
                )

            params: dict = {
                "to": input_data.to,
                "subject": input_data.subject,
                "text": input_data.text,
            }
            if input_data.html:
                params["html"] = input_data.html
            if input_data.cc:
                params["cc"] = input_data.cc
            if input_data.bcc:
                params["bcc"] = input_data.bcc
            if input_data.labels:
                params["labels"] = input_data.labels

            msg = await self.send_message(credentials, input_data.inbox_id, **params)
            result = msg.model_dump()

            yield "message_id", msg.message_id
            yield "thread_id", msg.thread_id or ""
            yield "result", result
        except Exception as e:
            yield "error", str(e)