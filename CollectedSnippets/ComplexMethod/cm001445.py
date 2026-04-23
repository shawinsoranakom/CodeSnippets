async def test_convert_to_step():
    now = datetime.now()
    step_model = StepModel(
        task_id="50da533e-3904-4401-8a07-c49adf88b5eb",
        step_id="6bb1801a-fd80-45e8-899a-4dd723cc602e",
        created_at=now,
        modified_at=now,
        name="Write to file",
        status="created",
        input="Write the words you receive to the file 'output.txt'.",
        additional_input={},
        artifacts=[
            ArtifactModel(
                artifact_id="b225e278-8b4c-4f99-a696-8facf19f0e56",
                created_at=now,
                modified_at=now,
                relative_path="file:///path/to/main.py",
                agent_created=True,
                file_name="main.py",
            )
        ],
        is_last=False,
    )
    step = convert_to_step(step_model)
    assert step.task_id == "50da533e-3904-4401-8a07-c49adf88b5eb"
    assert step.step_id == "6bb1801a-fd80-45e8-899a-4dd723cc602e"
    assert step.name == "Write to file"
    assert step.status == StepStatus.created
    assert len(step.artifacts) == 1
    assert step.artifacts[0].artifact_id == "b225e278-8b4c-4f99-a696-8facf19f0e56"
    assert step.is_last is False