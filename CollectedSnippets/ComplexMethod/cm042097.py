async def main(requirement="", enable_human_input=False, use_fixed_sop=False, allow_idle_time=30):
    if use_fixed_sop:
        engineer = Engineer(n_borg=5, use_code_review=False)
    else:
        engineer = Engineer2()

    env = MGXEnv()
    env.add_roles(
        [
            TeamLeader(),
            ProductManager(use_fixed_sop=use_fixed_sop),
            Architect(use_fixed_sop=use_fixed_sop),
            ProjectManager(use_fixed_sop=use_fixed_sop),
            engineer,
            # QaEngineer(),
            DataAnalyst(),
        ]
    )

    if enable_human_input:
        # simulate human sending messages in chatbox
        stop_event = threading.Event()
        human_input_thread = send_human_input(env, stop_event)

    if requirement:
        env.publish_message(Message(content=requirement))
        # user_defined_recipient = "Alex"
        # env.publish_message(Message(content=requirement, send_to={user_defined_recipient}), user_defined_recipient=user_defined_recipient)

    allow_idle_time = allow_idle_time if enable_human_input else 1
    start_time = time.time()
    while time.time() - start_time < allow_idle_time:
        if not env.is_idle:
            await env.run()
            start_time = time.time()  # reset start time

    if enable_human_input:
        print("No more human input, terminating, press ENTER for a full termination.")
        stop_event.set()
        human_input_thread.join()