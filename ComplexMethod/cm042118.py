async def test_plan_for_data_related_requirement(env):
    requirement = "I want to use yolov5 for target detection, yolov5 all the information from the following link, please help me according to the content of the link (https://github.com/ultralytics/yolov5), set up the environment and download the model parameters, and finally provide a few pictures for inference, the inference results will be saved!"

    tl = env.get_role("Mike")
    env.publish_message(Message(content=requirement, send_to=tl.name))
    await tl.run()

    history = env.history.get()
    messages_from_tl = [msg for msg in history if msg.sent_from == tl.name]
    da_messages = [msg for msg in messages_from_tl if "David" in msg.send_to]
    assert len(da_messages) > 0

    da_message = da_messages[0]
    assert "https://github.com/ultralytics/yolov5" in da_message.content

    def is_valid_task_message(msg: Message) -> bool:
        content = msg.content.lower()
        has_model_info = "yolov5" in content
        has_task_info = any(word in content for word in ["detection", "inference", "environment", "parameters"])
        has_link = "github.com" in content
        return has_model_info and has_task_info and has_link

    assert is_valid_task_message(da_message)