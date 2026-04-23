def test_get_ls_params() -> None:
    class LSParamsModel(BaseChatModel):
        model: str = "foo"
        temperature: float = 0.1
        max_tokens: int = 1024

        def _generate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            raise NotImplementedError

        @override
        def _stream(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> Iterator[ChatGenerationChunk]:
            raise NotImplementedError

        @property
        def _llm_type(self) -> str:
            return "fake-chat-model"

    llm = LSParamsModel()

    # Test standard tracing params
    ls_params = llm._get_ls_params()
    assert ls_params == {
        "ls_provider": "lsparamsmodel",
        "ls_model_type": "chat",
        "ls_model_name": "foo",
        "ls_temperature": 0.1,
        "ls_max_tokens": 1024,
    }

    ls_params = llm._get_ls_params(model="bar")
    assert ls_params["ls_model_name"] == "bar"

    ls_params = llm._get_ls_params(temperature=0.2)
    assert ls_params["ls_temperature"] == 0.2

    # Test integer temperature values (regression test for issue #35300)
    ls_params = llm._get_ls_params(temperature=0)
    assert ls_params["ls_temperature"] == 0

    ls_params = llm._get_ls_params(temperature=1)
    assert ls_params["ls_temperature"] == 1

    ls_params = llm._get_ls_params(max_tokens=2048)
    assert ls_params["ls_max_tokens"] == 2048

    ls_params = llm._get_ls_params(stop=["stop"])
    assert ls_params["ls_stop"] == ["stop"]