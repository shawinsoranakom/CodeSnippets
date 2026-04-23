async def test_magentic_one_group_chat_basic(runtime: AgentRuntime | None) -> None:
    agent_1 = _EchoAgent("agent_1", description="echo agent 1")
    agent_2 = _EchoAgent("agent_2", description="echo agent 2")
    agent_3 = _EchoAgent("agent_3", description="echo agent 3")
    agent_4 = _EchoAgent("agent_4", description="echo agent 4")

    model_client = ReplayChatCompletionClient(
        chat_completions=[
            "No facts",
            "No plan",
            json.dumps(
                {
                    "is_request_satisfied": {"answer": False, "reason": "test"},
                    "is_progress_being_made": {"answer": True, "reason": "test"},
                    "is_in_loop": {"answer": False, "reason": "test"},
                    "instruction_or_question": {"answer": "Continue task", "reason": "test"},
                    "next_speaker": {"answer": "agent_1", "reason": "test"},
                }
            ),
            json.dumps(
                {
                    "is_request_satisfied": {"answer": True, "reason": "Because"},
                    "is_progress_being_made": {"answer": True, "reason": "test"},
                    "is_in_loop": {"answer": False, "reason": "test"},
                    "instruction_or_question": {"answer": "Task completed", "reason": "Because"},
                    "next_speaker": {"answer": "agent_1", "reason": "test"},
                }
            ),
            "print('Hello, world!')",
        ],
    )

    team = MagenticOneGroupChat(
        participants=[agent_1, agent_2, agent_3, agent_4], model_client=model_client, runtime=runtime
    )
    result = await team.run(task="Write a program that prints 'Hello, world!'")
    assert len(result.messages) == 5
    assert result.messages[2].to_text() == "Continue task"
    assert result.messages[4].to_text() == "print('Hello, world!')"
    assert result.stop_reason is not None and result.stop_reason == "Because"

    # Test save and load.
    state = await team.save_state()
    team2 = MagenticOneGroupChat(
        participants=[agent_1, agent_2, agent_3, agent_4], model_client=model_client, runtime=runtime
    )
    await team2.load_state(state)
    state2 = await team2.save_state()
    assert state == state2
    manager_1 = await team._runtime.try_get_underlying_agent_instance(  # pyright: ignore
        AgentId(f"{team._group_chat_manager_name}_{team._team_id}", team._team_id),  # pyright: ignore
        MagenticOneOrchestrator,  # pyright: ignore
    )  # pyright: ignore
    manager_2 = await team2._runtime.try_get_underlying_agent_instance(  # pyright: ignore
        AgentId(f"{team2._group_chat_manager_name}_{team2._team_id}", team2._team_id),  # pyright: ignore
        MagenticOneOrchestrator,  # pyright: ignore
    )  # pyright: ignore
    assert manager_1._message_thread == manager_2._message_thread  # pyright: ignore
    assert manager_1._task == manager_2._task  # pyright: ignore
    assert manager_1._facts == manager_2._facts  # pyright: ignore
    assert manager_1._plan == manager_2._plan  # pyright: ignore
    assert manager_1._n_rounds == manager_2._n_rounds  # pyright: ignore
    assert manager_1._n_stalls == manager_2._n_stalls