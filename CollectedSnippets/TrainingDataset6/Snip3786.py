def endpoint(
        background_tasks: Annotated[BackgroundTasks, Depends(add_background_task)],
    ):
        background_tasks.add_task(background_task, "from endpoint")
        return {"status": "ok"}