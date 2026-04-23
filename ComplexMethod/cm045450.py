def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        *,
        tools: List[BaseTool[Any, Any] | Callable[..., Any] | Callable[..., Awaitable[Any]]] | None = None,
        workbench: Workbench | Sequence[Workbench] | None = None,
        handoffs: List[HandoffBase | str] | None = None,
        model_context: ChatCompletionContext | None = None,
        description: str = "An agent that provides assistance with ability to use tools.",
        system_message: (
            str | None
        ) = "You are a helpful AI assistant. Solve tasks using your tools. Reply with TERMINATE when the task has been completed.",
        model_client_stream: bool = False,
        reflect_on_tool_use: bool | None = None,
        max_tool_iterations: int = 1,
        tool_call_summary_format: str = "{result}",
        tool_call_summary_formatter: Callable[[FunctionCall, FunctionExecutionResult], str] | None = None,
        output_content_type: type[BaseModel] | None = None,
        output_content_type_format: str | None = None,
        memory: Sequence[Memory] | None = None,
        metadata: Dict[str, str] | None = None,
    ):
        super().__init__(name=name, description=description)
        self._metadata = metadata or {}
        self._model_client = model_client
        self._model_client_stream = model_client_stream
        self._output_content_type: type[BaseModel] | None = output_content_type
        self._output_content_type_format = output_content_type_format
        self._structured_message_factory: StructuredMessageFactory | None = None
        if output_content_type is not None:
            self._structured_message_factory = StructuredMessageFactory(
                input_model=output_content_type, format_string=output_content_type_format
            )

        self._memory = None
        if memory is not None:
            if isinstance(memory, list):
                self._memory = memory
            else:
                raise TypeError(f"Expected Memory, List[Memory], or None, got {type(memory)}")

        self._system_messages: List[SystemMessage] = []
        if system_message is None:
            self._system_messages = []
        else:
            self._system_messages = [SystemMessage(content=system_message)]
        self._tools: List[BaseTool[Any, Any]] = []
        if tools is not None:
            if model_client.model_info["function_calling"] is False:
                raise ValueError("The model does not support function calling.")
            for tool in tools:
                if isinstance(tool, BaseTool):
                    self._tools.append(tool)
                elif callable(tool):
                    if hasattr(tool, "__doc__") and tool.__doc__ is not None:
                        description = tool.__doc__
                    else:
                        description = ""
                    self._tools.append(FunctionTool(tool, description=description))
                else:
                    raise ValueError(f"Unsupported tool type: {type(tool)}")
        # Check if tool names are unique.
        tool_names = [tool.name for tool in self._tools]
        if len(tool_names) != len(set(tool_names)):
            raise ValueError(f"Tool names must be unique: {tool_names}")

        # Handoff tools.
        self._handoff_tools: List[BaseTool[Any, Any]] = []
        self._handoffs: Dict[str, HandoffBase] = {}
        if handoffs is not None:
            if model_client.model_info["function_calling"] is False:
                raise ValueError("The model does not support function calling, which is needed for handoffs.")
            for handoff in handoffs:
                if isinstance(handoff, str):
                    handoff = HandoffBase(target=handoff)
                if isinstance(handoff, HandoffBase):
                    self._handoff_tools.append(handoff.handoff_tool)
                    self._handoffs[handoff.name] = handoff
                else:
                    raise ValueError(f"Unsupported handoff type: {type(handoff)}")
        # Check if handoff tool names are unique.
        handoff_tool_names = [tool.name for tool in self._handoff_tools]
        if len(handoff_tool_names) != len(set(handoff_tool_names)):
            raise ValueError(f"Handoff names must be unique: {handoff_tool_names}")
        # Create sets for faster lookup
        tool_names_set = set(tool_names)
        handoff_tool_names_set = set(handoff_tool_names)

        # Check if there's any overlap between handoff tool names and tool names
        overlap = tool_names_set.intersection(handoff_tool_names_set)

        # Also check if any handoff target name matches a tool name
        # This handles the case where a handoff is specified directly with a string that matches a tool name
        for handoff in handoffs or []:
            if isinstance(handoff, str) and handoff in tool_names_set:
                raise ValueError("Handoff names must be unique from tool names")
            elif isinstance(handoff, HandoffBase) and handoff.target in tool_names_set:
                raise ValueError("Handoff names must be unique from tool names")

        if overlap:
            raise ValueError("Handoff names must be unique from tool names")

        if workbench is not None:
            if self._tools:
                raise ValueError("Tools cannot be used with a workbench.")
            if isinstance(workbench, Sequence):
                self._workbench = workbench
            else:
                self._workbench = [workbench]
        else:
            self._workbench = [StaticStreamWorkbench(self._tools)]

        if model_context is not None:
            self._model_context = model_context
        else:
            self._model_context = UnboundedChatCompletionContext()

        if self._output_content_type is not None and reflect_on_tool_use is None:
            # If output_content_type is set, we need to reflect on tool use by default.
            self._reflect_on_tool_use = True
        elif reflect_on_tool_use is None:
            self._reflect_on_tool_use = False
        else:
            self._reflect_on_tool_use = reflect_on_tool_use

        # Tool call loop
        self._max_tool_iterations = max_tool_iterations
        if self._max_tool_iterations < 1:
            raise ValueError(
                f"Maximum number of tool iterations must be greater than or equal to 1, got {max_tool_iterations}"
            )

        self._tool_call_summary_format = tool_call_summary_format
        self._tool_call_summary_formatter = tool_call_summary_formatter
        self._is_running = False