def test_responses_integration_matrix(case: TestCase) -> None:
    if case.name == "asking for information that does not fit into the response format":
        pytest.xfail(
            "currently failing due to undefined behavior when model cannot conform to "
            "any of the structured response formats."
        )

    def get_employee_role(*, name: str) -> str | None:
        for e in EMPLOYEES:
            if e.name == name:
                return e.role
        return None

    def get_employee_department(*, name: str) -> str | None:
        for e in EMPLOYEES:
            if e.name == name:
                return e.department
        return None

    role_tool = _make_tool(
        get_employee_role,
        name="get_employee_role",
        description="Get the employee role by name",
    )
    dept_tool = _make_tool(
        get_employee_department,
        name="get_employee_department",
        description="Get the employee department by name",
    )

    response_format_spec = case.response_format
    if isinstance(response_format_spec, dict):
        response_format_spec = [response_format_spec]
    # Unwrap nested schema objects
    response_format_spec = [item.get("schema", item) for item in response_format_spec]
    if len(response_format_spec) == 1:
        tool_output = ToolStrategy(response_format_spec[0])
    else:
        tool_output = ToolStrategy({"oneOf": response_format_spec})

    llm_request_count = 0

    for assertion in case.assertions_by_invocation:

        def on_request(_request: httpx.Request) -> None:
            nonlocal llm_request_count
            llm_request_count += 1

        http_client = httpx.Client(
            event_hooks={"request": [on_request]},
        )

        model = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            http_client=http_client,
        )

        agent = create_agent(
            model,
            tools=[role_tool["tool"], dept_tool["tool"]],
            system_prompt=AGENT_PROMPT,
            response_format=tool_output,
        )

        result = agent.invoke({"messages": [HumanMessage(assertion.prompt)]})

        # Count tool calls
        assert role_tool["mock"].call_count == assertion.tools_with_expected_calls.get_employee_role
        assert (
            dept_tool["mock"].call_count
            == assertion.tools_with_expected_calls.get_employee_department
        )

        # Count LLM calls
        assert llm_request_count == assertion.llm_request_count

        # Check last message content
        last_message = result["messages"][-1]
        assert last_message.content == assertion.expected_last_message

        # Check structured response
        structured_response_json = result["structured_response"]
        assert structured_response_json == assertion.expected_structured_response