async def lifespan(_app: FastAPI):
        from lfx.interface.components import get_and_cache_all_types_dict

        configure()

        # Startup message
        if version:
            await logger.adebug(f"Starting Langflow v{version}...")
        else:
            await logger.adebug("Starting Langflow...")

        temp_dirs: list[TemporaryDirectory] = []
        sync_flows_from_fs_task = None
        mcp_init_task = None

        try:
            start_time = asyncio.get_event_loop().time()

            await logger.adebug("Initializing services")
            await initialize_services(fix_migration=fix_migration)
            await logger.adebug(f"Services initialized in {asyncio.get_event_loop().time() - start_time:.2f}s")

            current_time = asyncio.get_event_loop().time()
            await logger.adebug("Setting up LLM caching")
            setup_llm_caching()
            await logger.adebug(f"LLM caching setup in {asyncio.get_event_loop().time() - current_time:.2f}s")

            current_time = asyncio.get_event_loop().time()
            await logger.adebug("Copying profile pictures")
            await copy_profile_pictures()
            await logger.adebug(f"Profile pictures copied in {asyncio.get_event_loop().time() - current_time:.2f}s")

            if get_settings_service().auth_settings.AUTO_LOGIN:
                current_time = asyncio.get_event_loop().time()
                await logger.adebug("Initializing default super user")
                await initialize_auto_login_default_superuser()
                await logger.adebug(
                    f"Default super user initialized in {asyncio.get_event_loop().time() - current_time:.2f}s"
                )

            await logger.adebug("Initializing super user")
            await initialize_auto_login_default_superuser()
            await logger.adebug(f"Super user initialized in {asyncio.get_event_loop().time() - current_time:.2f}s")

            current_time = asyncio.get_event_loop().time()
            await logger.adebug("Loading bundles")
            temp_dirs, bundles_components_paths = await load_bundles_with_error_handling()
            get_settings_service().settings.components_path.extend(bundles_components_paths)
            await logger.adebug(f"Bundles loaded in {asyncio.get_event_loop().time() - current_time:.2f}s")

            current_time = asyncio.get_event_loop().time()
            await logger.adebug("Caching types")
            all_types_dict = await get_and_cache_all_types_dict(get_settings_service(), telemetry_service)
            await logger.adebug(f"Types cached in {asyncio.get_event_loop().time() - current_time:.2f}s")

            # Use file-based lock to prevent multiple workers from creating duplicate starter projects concurrently.
            # Note that it's still possible that one worker may complete this task, release the lock,
            # then another worker pick it up, but the operation is idempotent so worst case it duplicates
            # the initialization work.
            current_time = asyncio.get_event_loop().time()
            await logger.adebug("Creating/updating starter projects")

            lock_file = Path(tempfile.gettempdir()) / "langflow_starter_projects.lock"
            lock = FileLock(lock_file, timeout=1)
            try:
                with lock:
                    await create_or_update_starter_projects(all_types_dict)
                    await logger.adebug(
                        f"Starter projects created/updated in {asyncio.get_event_loop().time() - current_time:.2f}s"
                    )
            except TimeoutError:
                # Another process has the lock
                await logger.adebug("Another worker is creating starter projects, skipping")
            except Exception as e:  # noqa: BLE001
                await logger.awarning(
                    f"Failed to acquire lock for starter projects: {e}. Starter projects may not be created or updated."
                )

            # Initialize agentic global variables early (before MCP server and flows)
            if get_settings_service().settings.agentic_experience:
                from langflow.api.utils.mcp.agentic_mcp import initialize_agentic_global_variables

                current_time = asyncio.get_event_loop().time()
                await logger.ainfo("Initializing agentic global variables...")
                try:
                    async with session_scope() as session:
                        await initialize_agentic_global_variables(session)
                    await logger.adebug(
                        f"Agentic global variables initialized in {asyncio.get_event_loop().time() - current_time:.2f}s"
                    )
                except Exception as e:  # noqa: BLE001
                    await logger.awarning(f"Failed to initialize agentic global variables: {e}")

            current_time = asyncio.get_event_loop().time()
            await logger.adebug("Starting telemetry service")
            telemetry_service.start()
            await logger.adebug(f"started telemetry service in {asyncio.get_event_loop().time() - current_time:.2f}s")

            current_time = asyncio.get_event_loop().time()
            await logger.adebug("Starting MCP Composer service")
            mcp_composer_service = cast("MCPComposerService", get_service(ServiceType.MCP_COMPOSER_SERVICE))
            await mcp_composer_service.start()
            await logger.adebug(
                f"started MCP Composer service in {asyncio.get_event_loop().time() - current_time:.2f}s"
            )

            # Auto-configure Agentic MCP server if enabled (after variables are initialized)
            if get_settings_service().settings.agentic_experience:
                from langflow.api.utils.mcp.agentic_mcp import auto_configure_agentic_mcp_server

                current_time = asyncio.get_event_loop().time()
                await logger.ainfo("Configuring Agentic MCP server...")
                try:
                    async with session_scope() as session:
                        await auto_configure_agentic_mcp_server(session)
                    await logger.adebug(
                        f"Agentic MCP server configured in {asyncio.get_event_loop().time() - current_time:.2f}s"
                    )
                except Exception as e:  # noqa: BLE001
                    await logger.awarning(f"Failed to configure agentic MCP server: {e}")

            current_time = asyncio.get_event_loop().time()
            await logger.adebug("Loading flows")
            await load_flows_from_directory()
            sync_flows_from_fs_task = asyncio.create_task(sync_flows_from_fs())
            queue_service = get_queue_service()
            if not queue_service.is_started():  # Start if not already started
                queue_service.start()
            await logger.adebug(f"Flows loaded in {asyncio.get_event_loop().time() - current_time:.2f}s")

            total_time = asyncio.get_event_loop().time() - start_time
            await logger.adebug(f"Total initialization time: {total_time:.2f}s")

            async def delayed_init_mcp_servers():
                await asyncio.sleep(10.0)  # Increased delay to allow starter projects to be created
                current_time = asyncio.get_event_loop().time()
                await logger.adebug("Loading MCP servers for projects")
                try:
                    await init_mcp_servers()
                    await logger.adebug(f"MCP servers loaded in {asyncio.get_event_loop().time() - current_time:.2f}s")
                except Exception as e:  # noqa: BLE001
                    await logger.awarning(f"First MCP server initialization attempt failed: {e}")
                    await asyncio.sleep(5.0)  # Increased retry delay
                    current_time = asyncio.get_event_loop().time()
                    await logger.adebug("Retrying MCP servers initialization")
                    try:
                        await init_mcp_servers()
                        await logger.adebug(
                            f"MCP servers loaded on retry in {asyncio.get_event_loop().time() - current_time:.2f}s"
                        )
                    except Exception as e2:  # noqa: BLE001
                        await logger.aexception(f"Failed to initialize MCP servers after retry: {e2}")

            # Start the delayed initialization as a background task
            # Allows the server to start first to avoid race conditions with MCP Server startup
            mcp_init_task = asyncio.create_task(delayed_init_mcp_servers())

            # v1 and project MCP server context managers
            from langflow.api.v1.mcp import start_streamable_http_manager
            from langflow.api.v1.mcp_projects import start_project_task_group

            await start_streamable_http_manager()
            await start_project_task_group()

            yield
        except asyncio.CancelledError:
            await logger.adebug("Lifespan received cancellation signal")
        except UnsupportedPostgreSQLVersionError:
            # Normally caught by the pre-flight check in __main__.py
            # before the server starts.  If we get here anyway (e.g.
            # direct uvicorn invocation via ``make backend``), exit
            # immediately and tell the parent (reloader) to stop.
            import signal

            sys.stdout.flush()
            sys.stderr.flush()
            with suppress(ProcessLookupError, PermissionError):
                os.kill(os.getppid(), signal.SIGTERM)
            os._exit(3)
        except Exception as exc:
            if "langflow migration --fix" not in str(exc):
                logger.exception(exc)

                await log_exception_to_telemetry(exc, "lifespan")
            raise
        finally:
            # CRITICAL: Cleanup MCP sessions FIRST, before any other shutdown logic.
            # This ensures MCP subprocesses are killed even if shutdown is interrupted.
            await cleanup_mcp_sessions()

            # Clean shutdown with progress indicator
            # Create shutdown progress (show verbose timing if log level is DEBUG)
            from langflow.__main__ import get_number_of_workers
            from langflow.cli.progress import create_langflow_shutdown_progress

            log_level = os.getenv("LANGFLOW_LOG_LEVEL", "info").lower()
            num_workers = get_number_of_workers(get_settings_service().settings.workers)
            shutdown_progress = create_langflow_shutdown_progress(
                verbose=log_level == "debug", multiple_workers=num_workers > 1
            )

            try:
                # Step 0: Stopping Server
                with shutdown_progress.step(0):
                    await logger.adebug("Stopping server gracefully...")
                    # The actual server stopping is handled by the lifespan context
                    await asyncio.sleep(0.1)  # Brief pause for visual effect

                # Step 1: Cancelling Background Tasks
                with shutdown_progress.step(1):
                    from langflow.api.v1.mcp import stop_streamable_http_manager
                    from langflow.api.v1.mcp_projects import stop_project_task_group

                    # Shutdown MCP project servers
                    try:
                        await stop_project_task_group()
                    except Exception as e:  # noqa: BLE001
                        await logger.aerror(f"Failed to stop MCP Project servers: {e}")
                    # Close MCP server streamable-http session manager .run() context manager
                    try:
                        await stop_streamable_http_manager()
                    except Exception as e:  # noqa: BLE001
                        await logger.aerror(f"Failed to stop MCP server streamable-http session manager: {e}")
                    # Cancel background tasks
                    tasks_to_cancel = []
                    if sync_flows_from_fs_task:
                        sync_flows_from_fs_task.cancel()
                        tasks_to_cancel.append(sync_flows_from_fs_task)
                    if mcp_init_task and not mcp_init_task.done():
                        mcp_init_task.cancel()
                        tasks_to_cancel.append(mcp_init_task)
                    if tasks_to_cancel:
                        # Wait for all tasks to complete, capturing exceptions
                        results = await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
                        # Log any non-cancellation exceptions
                        for result in results:
                            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                                await logger.aerror(f"Error during task cleanup: {result}", exc_info=result)

                # Step 2: Cleaning Up Services
                with shutdown_progress.step(2):
                    try:
                        await asyncio.wait_for(teardown_services(), timeout=30)
                    except asyncio.TimeoutError:
                        await logger.awarning("Teardown services timed out after 30s.")

                # Step 3: Clearing Temporary Files
                with shutdown_progress.step(3):
                    temp_dir_cleanups = [asyncio.to_thread(temp_dir.cleanup) for temp_dir in temp_dirs]
                    try:
                        await asyncio.wait_for(asyncio.gather(*temp_dir_cleanups), timeout=10)
                    except asyncio.TimeoutError:
                        await logger.awarning("Temporary file cleanup timed out after 10s.")

                # Step 4: Finalizing Shutdown
                with shutdown_progress.step(4):
                    await logger.adebug("Langflow shutdown complete")

                # Show completion summary and farewell
                shutdown_progress.print_shutdown_summary()

            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.DBAPIError) as e:
                # Case where the database connection is closed during shutdown
                await logger.awarning(f"Database teardown failed due to closed connection: {e}")
            except asyncio.CancelledError:
                # Swallow this - it's normal during shutdown
                await logger.adebug("Teardown cancelled during shutdown.")
            except Exception as e:  # noqa: BLE001
                await logger.aexception(f"Unhandled error during cleanup: {e}")
                await log_exception_to_telemetry(e, "lifespan_cleanup")