def __init__(
        self,
        name: str,
        description: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
        model: str,
        instructions: str,
        tools: Optional[
            Iterable[
                Union[
                    Literal["code_interpreter", "file_search"],
                    Tool | Callable[..., Any] | Callable[..., Awaitable[Any]],
                ]
            ]
        ] = None,
        assistant_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        response_format: Optional["AssistantResponseFormatOptionParam"] = None,
        temperature: Optional[float] = None,
        tool_resources: Optional["ToolResources"] = None,
        top_p: Optional[float] = None,
    ) -> None:
        if isinstance(client, ChatCompletionClient):
            raise ValueError(
                "Incorrect client passed to OpenAIAssistantAgent. Please use an OpenAI AsyncClient instance instead of an AutoGen ChatCompletionClient instance."
            )

        super().__init__(name, description)
        if tools is None:
            tools = []

        # Store original tools and converted tools separately
        self._original_tools: List[Tool] = []
        converted_tools: List["AssistantToolParam"] = []
        for tool in tools:
            if isinstance(tool, str):
                if tool == "code_interpreter":
                    converted_tools.append(CodeInterpreterToolParam(type="code_interpreter"))
                elif tool == "file_search":
                    converted_tools.append(FileSearchToolParam(type="file_search"))
            elif isinstance(tool, Tool):
                self._original_tools.append(tool)
                converted_tools.append(_convert_tool_to_function_param(tool))
            elif callable(tool):
                if hasattr(tool, "__doc__") and tool.__doc__ is not None:
                    description = tool.__doc__
                else:
                    description = ""
                function_tool = FunctionTool(tool, description=description)
                self._original_tools.append(function_tool)
                converted_tools.append(_convert_tool_to_function_param(function_tool))
            else:
                raise ValueError(f"Unsupported tool type: {type(tool)}")

        self._client = client
        self._assistant: Optional["Assistant"] = None
        self._thread: Optional["Thread"] = None
        self._init_thread_id = thread_id
        self._model = model
        self._instructions = instructions
        self._api_tools = converted_tools
        self._assistant_id = assistant_id
        self._metadata = metadata
        self._response_format = response_format
        self._temperature = temperature
        self._tool_resources = tool_resources
        self._top_p = top_p
        self._vector_store_id: Optional[str] = None
        self._uploaded_file_ids: List[str] = []

        # Variables to track initial state
        self._initial_message_ids: Set[str] = set()
        self._initial_state_retrieved: bool = False