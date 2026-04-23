async def dispatch_tasks():
    while True:
        try:
            list(SyncLogsService.list_sync_tasks()[0])
            break
        except Exception as e:
            logging.warning(f"DB is not ready yet: {e}")
            await asyncio.sleep(3)

    tasks = []
    for task in SyncLogsService.list_sync_tasks()[0]:
        if task["poll_range_start"]:
            task["poll_range_start"] = task["poll_range_start"].astimezone(timezone.utc)
        if task["poll_range_end"]:
            task["poll_range_end"] = task["poll_range_end"].astimezone(timezone.utc)
        func = func_factory[task["source"]](task["config"])
        tasks.append(asyncio.create_task(func(task)))

    try:
        await asyncio.gather(*tasks, return_exceptions=False)
    except Exception as e:
        logging.error(f"Error in dispatch_tasks: {e}")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    await asyncio.sleep(1)