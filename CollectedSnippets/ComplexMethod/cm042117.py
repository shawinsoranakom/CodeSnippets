async def test_plan_for_software_requirement(env):
    requirement = "create a 2048 game"
    tl = env.get_role("Mike")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    history = env.history.get()

    messages_to_team = [msg for msg in history if msg.sent_from == tl.name]
    pm_messages = [msg for msg in messages_to_team if "Alice" in msg.send_to]
    assert len(pm_messages) > 0, "Should have message sent to Product Manager"
    found_task_msg = False
    for msg in messages_to_team:
        if "prd" in msg.content.lower() and any(role in msg.content for role in ["Alice", "Bob", "Alex", "David"]):
            found_task_msg = True
            break
    assert found_task_msg, "Should have task assignment message"