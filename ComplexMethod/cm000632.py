async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            params: dict = {"to": input_data.to}
            if input_data.subject:
                params["subject"] = input_data.subject
            if input_data.text:
                params["text"] = input_data.text
            if input_data.html:
                params["html"] = input_data.html
            if input_data.cc:
                params["cc"] = input_data.cc
            if input_data.bcc:
                params["bcc"] = input_data.bcc
            if input_data.in_reply_to:
                params["in_reply_to"] = input_data.in_reply_to
            if input_data.send_at:
                params["send_at"] = input_data.send_at

            draft = await self.create_draft(credentials, input_data.inbox_id, **params)
            result = draft.model_dump()

            yield "draft_id", draft.draft_id
            yield "send_status", draft.send_status or ""
            yield "result", result
        except Exception as e:
            yield "error", str(e)