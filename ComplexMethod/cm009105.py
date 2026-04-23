def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        self._ensure_sync_client_available()
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        generation_info = None
        raw_response = None
        try:
            if "response_format" in payload:
                payload.pop("stream")
                raw_response = (
                    self.root_client.chat.completions.with_raw_response.parse(**payload)
                )
                response = raw_response.parse()
            elif self._use_responses_api(payload):
                original_schema_obj = kwargs.get("response_format")
                if original_schema_obj and _is_pydantic_class(original_schema_obj):
                    raw_response = self.root_client.responses.with_raw_response.parse(
                        **payload
                    )
                else:
                    raw_response = self.root_client.responses.with_raw_response.create(
                        **payload
                    )
                response = raw_response.parse()
                if self.include_response_headers:
                    generation_info = {"headers": dict(raw_response.headers)}
                return _construct_lc_result_from_responses_api(
                    response,
                    schema=original_schema_obj,
                    metadata=generation_info,
                    output_version=self.output_version,
                )
            else:
                raw_response = self.client.with_raw_response.create(**payload)
                response = raw_response.parse()
        except openai.BadRequestError as e:
            _handle_openai_bad_request(e)
        except openai.APIError as e:
            _handle_openai_api_error(e)
        except Exception as e:
            if raw_response is not None and hasattr(raw_response, "http_response"):
                e.response = raw_response.http_response  # type: ignore[attr-defined]
            raise e
        if (
            self.include_response_headers
            and raw_response is not None
            and hasattr(raw_response, "headers")
        ):
            generation_info = {"headers": dict(raw_response.headers)}
        return self._create_chat_result(response, generation_info)