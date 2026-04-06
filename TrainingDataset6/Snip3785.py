def add_background_task(background_tasks: BackgroundTasks) -> BackgroundTasks:
        background_tasks.add_task(background_task, "from dependency")
        return background_tasks