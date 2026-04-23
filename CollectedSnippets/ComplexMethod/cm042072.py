async def test_react():
    class Input(BaseModel):
        name: str
        profile: str
        goal: str
        constraints: str
        desc: str
        address: str

    inputs = [
        {
            "name": "A",
            "profile": "Tester",
            "goal": "Test",
            "constraints": "constraints",
            "desc": "desc",
            "address": "start",
        }
    ]

    for i in inputs:
        seed = Input(**i)
        role = MockRole(
            name=seed.name, profile=seed.profile, goal=seed.goal, constraints=seed.constraints, desc=seed.desc
        )
        role.set_addresses({seed.address})
        assert role.rc.watch == {any_to_str(UserRequirement)}
        assert role.name == seed.name
        assert role.profile == seed.profile
        assert role.goal == seed.goal
        assert role.constraints == seed.constraints
        assert role.desc == seed.desc
        assert role.is_idle
        env = Environment()
        env.add_role(role)
        assert env.get_addresses(role) == {seed.address}
        env.publish_message(Message(content="test", msg_to=seed.address))
        assert not role.is_idle
        while not env.is_idle:
            await env.run()
        assert role.is_idle
        env.publish_message(Message(content="test", cause_by=seed.address))
        assert not role.is_idle
        while not env.is_idle:
            await env.run()
        assert role.is_idle
        tag = uuid.uuid4().hex
        role.set_addresses({tag})
        assert env.get_addresses(role) == {tag}