def _validate_create_responses_input(
        self, request: ResponsesRequest
    ) -> ErrorResponse | None:
        if self.use_harmony and request.is_include_output_logprobs():
            return self.create_error_response(
                err_type="invalid_request_error",
                message="logprobs are not supported with gpt-oss models",
                status_code=HTTPStatus.BAD_REQUEST,
                param="logprobs",
            )
        if request.store and not self.enable_store and request.background:
            return self.create_error_response(
                err_type="invalid_request_error",
                message=(
                    "This vLLM engine does not support `store=True` and "
                    "therefore does not support the background mode. To "
                    "enable these features, set the environment variable "
                    "`VLLM_ENABLE_RESPONSES_API_STORE=1` when launching "
                    "the vLLM server."
                ),
                status_code=HTTPStatus.BAD_REQUEST,
                param="background",
            )
        if request.previous_input_messages and request.previous_response_id:
            return self.create_error_response(
                err_type="invalid_request_error",
                message="Only one of `previous_input_messages` and "
                "`previous_response_id` can be set.",
                status_code=HTTPStatus.BAD_REQUEST,
                param="previous_response_id",
            )
        return None