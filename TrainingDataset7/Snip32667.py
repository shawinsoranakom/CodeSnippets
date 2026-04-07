def test_context(context, attempt):
    assert isinstance(context, TaskContext)
    assert context.attempt == attempt