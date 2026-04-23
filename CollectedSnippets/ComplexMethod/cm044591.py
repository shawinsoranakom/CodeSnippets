def test_reset() -> None:
    progress = Progress()
    task_id = progress.add_task("foo")
    progress.advance(task_id, 1)
    progress.advance(task_id, 1)
    progress.advance(task_id, 1)
    progress.advance(task_id, 7)
    task = progress.tasks[task_id]
    assert task.completed == 10
    progress.reset(
        task_id,
        total=200,
        completed=20,
        visible=False,
        description="bar",
        example="egg",
    )
    assert task.total == 200
    assert task.completed == 20
    assert task.visible == False
    assert task.description == "bar"
    assert task.fields == {"example": "egg"}
    assert not task._progress