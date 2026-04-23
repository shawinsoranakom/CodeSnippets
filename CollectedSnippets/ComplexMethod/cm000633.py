async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            params: dict = {}
            if input_data.to is not None:
                params["to"] = input_data.to
            if input_data.subject is not None:
                params["subject"] = input_data.subject
            if input_data.text is not None:
                params["text"] = input_data.text
            if input_data.html is not None:
                params["html"] = input_data.html
            if input_data.send_at is not None:
                params["send_at"] = input_data.send_at

            draft = await self.update_draft(
                credentials, input_data.inbox_id, input_data.draft_id, **params
            )
            result = draft.model_dump()

            yield "draft_id", draft.draft_id
            yield "send_status", draft.send_status or ""
            yield "result", result
        except Exception as e:
            yield "error", str(e)