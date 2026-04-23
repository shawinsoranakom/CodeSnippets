async def sync_flows_from_fs():
    flow_mtimes = {}
    fs_flows_polling_interval = get_settings_service().settings.fs_flows_polling_interval / 1000
    storage_service = get_storage_service()
    try:
        while True:
            try:
                async with session_scope() as session:
                    stmt = select(Flow).where(col(Flow.fs_path).is_not(None))
                    flows = (await session.exec(stmt)).all()
                    for flow in flows:
                        mtime = flow_mtimes.setdefault(flow.id, 0)
                        # Resolve path: if relative, construct full path using user's flows directory
                        fs_path_str = flow.fs_path
                        if not Path(fs_path_str).is_absolute():
                            # Relative path - construct full path
                            path = storage_service.data_dir / "flows" / str(flow.user_id) / fs_path_str
                        else:
                            # Absolute path - use as-is
                            path = anyio.Path(fs_path_str)
                        try:
                            if await path.exists():
                                new_mtime = (await path.stat()).st_mtime
                                if new_mtime > mtime:
                                    update_data = orjson.loads(await path.read_text(encoding="utf-8"))
                                    try:
                                        for field_name in ("name", "description", "data", "locked"):
                                            if new_value := update_data.get(field_name):
                                                setattr(flow, field_name, new_value)
                                        if folder_id := update_data.get("folder_id"):
                                            flow.folder_id = UUID(folder_id)
                                        await session.flush()
                                        await session.refresh(flow)
                                    except Exception:  # noqa: BLE001
                                        await logger.aexception(
                                            f"Couldn't update flow {flow.id} in database from path {path}"
                                        )
                                    flow_mtimes[flow.id] = new_mtime
                        except Exception:  # noqa: BLE001
                            await logger.aexception(f"Error while handling flow file {path}")
            except asyncio.CancelledError:
                await logger.adebug("Flow sync cancelled")
                break
            except (sa.exc.OperationalError, ValueError) as e:
                if "no active connection" in str(e) or "connection is closed" in str(e):
                    await logger.adebug("Database connection lost, assuming shutdown")
                    break  # Exit gracefully, don't error
                raise  # Re-raise if it's a real connection problem
            except Exception:  # noqa: BLE001
                await logger.aexception("Error while syncing flows from database")
                break

            await asyncio.sleep(fs_flows_polling_interval)
    except asyncio.CancelledError:
        await logger.adebug("Flow sync task cancelled")