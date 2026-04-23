def _use_responses_api(self, payload: dict) -> bool:
        if isinstance(self.use_responses_api, bool):
            return self.use_responses_api
        if (
            self.output_version == "responses/v1"
            or self.context_management is not None
            or self.include is not None
            or self.reasoning is not None
            or self.truncation is not None
            or self.use_previous_response_id
            or _model_prefers_responses_api(self.model_name)
        ):
            return True
        return _use_responses_api(payload)