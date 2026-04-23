async def test_step_schema():
    now = datetime.now()
    step = Step(
        task_id="50da533e-3904-4401-8a07-c49adf88b5eb",
        step_id="6bb1801a-fd80-45e8-899a-4dd723cc602e",
        created_at=now,
        modified_at=now,
        name="Write to file",
        input="Write the words you receive to the file 'output.txt'.",
        status=StepStatus.created,
        output=(
            "I am going to use the write_to_file command and write Washington "
            "to a file called output.txt <write_to_file('output.txt', 'Washington')>"
        ),
        artifacts=[
            Artifact(
                artifact_id="b225e278-8b4c-4f99-a696-8facf19f0e56",
                file_name="main.py",
                relative_path="python/code/",
                created_at=now,
                modified_at=now,
                agent_created=True,
            )
        ],
        is_last=False,
    )
    assert step.task_id == "50da533e-3904-4401-8a07-c49adf88b5eb"
    assert step.step_id == "6bb1801a-fd80-45e8-899a-4dd723cc602e"
    assert step.name == "Write to file"
    assert step.status == StepStatus.created
    assert step.output == (
        "I am going to use the write_to_file command and write Washington "
        "to a file called output.txt <write_to_file('output.txt', 'Washington')>"
    )
    assert len(step.artifacts) == 1
    assert step.artifacts[0].artifact_id == "b225e278-8b4c-4f99-a696-8facf19f0e56"
    assert step.is_last is False