def test_nonlocals() -> None:
    agent = RunnableLambda[str, str](lambda x: x * 2)

    def my_func(value: str, agent: dict[str, str]) -> str:
        return agent.get("agent_name", value)

    def my_func2(value: str) -> str:
        return str(agent.get("agent_name", value))  # type: ignore[attr-defined]

    def my_func3(value: str) -> str:
        return agent.invoke(value)

    def my_func4(value: str) -> str:
        return global_agent.invoke(value)

    def my_func5() -> tuple[Callable[[str], str], RunnableLambda]:
        global_agent = RunnableLambda[str, str](lambda x: x * 3)

        def my_func6(value: str) -> str:
            return global_agent.invoke(value)

        return my_func6, global_agent

    assert get_function_nonlocals(my_func) == []
    assert get_function_nonlocals(my_func2) == []
    assert get_function_nonlocals(my_func3) == [agent.invoke]
    assert get_function_nonlocals(my_func4) == [global_agent.invoke]
    func, nl = my_func5()
    assert get_function_nonlocals(func) == [nl.invoke]
    assert RunnableLambda(my_func3).deps == [agent]
    assert RunnableLambda(my_func4).deps == [global_agent]
    assert RunnableLambda(func).deps == [nl]