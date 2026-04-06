def test_background_tasks_with_depends_annotated():
    """BackgroundTasks type hint should work with Annotated[BackgroundTasks, Depends(...)]."""
    app = FastAPI()
    task_results = []

    def background_task(message: str):
        task_results.append(message)

    def add_background_task(background_tasks: BackgroundTasks) -> BackgroundTasks:
        background_tasks.add_task(background_task, "from dependency")
        return background_tasks

    @app.get("/")
    def endpoint(
        background_tasks: Annotated[BackgroundTasks, Depends(add_background_task)],
    ):
        background_tasks.add_task(background_task, "from endpoint")
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.get("/")

    assert resp.status_code == 200
    assert "from dependency" in task_results
    assert "from endpoint" in task_results