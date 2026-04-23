def start_comfyui(asyncio_loop=None):
    """
    Starts the ComfyUI server using the provided asyncio event loop or creates a new one.
    Returns the event loop, server instance, and a function to start the server asynchronously.
    """
    if args.temp_directory:
        temp_dir = os.path.join(os.path.abspath(args.temp_directory), "temp")
        logging.info(f"Setting temp directory to: {temp_dir}")
        folder_paths.set_temp_directory(temp_dir)
    cleanup_temp()

    if args.windows_standalone_build:
        try:
            import new_updater
            new_updater.update_windows_updater()
        except:
            pass

    if not asyncio_loop:
        asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(asyncio_loop)
    prompt_server = server.PromptServer(asyncio_loop)

    if args.enable_manager and not args.disable_manager_ui:
        comfyui_manager.start()

    hook_breaker_ac10a0.save_functions()
    asyncio_loop.run_until_complete(nodes.init_extra_nodes(
        init_custom_nodes=(not args.disable_all_custom_nodes) or len(args.whitelist_custom_nodes) > 0,
        init_api_nodes=not args.disable_api_nodes
    ))
    hook_breaker_ac10a0.restore_functions()

    cuda_malloc_warning()
    setup_database()

    prompt_server.add_routes()
    hijack_progress(prompt_server)

    threading.Thread(target=prompt_worker, daemon=True, args=(prompt_server.prompt_queue, prompt_server,)).start()

    if args.quick_test_for_ci:
        exit(0)

    os.makedirs(folder_paths.get_temp_directory(), exist_ok=True)
    call_on_start = None
    if args.auto_launch:
        def startup_server(scheme, address, port):
            import webbrowser
            if os.name == 'nt' and address == '0.0.0.0':
                address = '127.0.0.1'
            if ':' in address:
                address = "[{}]".format(address)
            webbrowser.open(f"{scheme}://{address}:{port}")
        call_on_start = startup_server

    async def start_all():
        await prompt_server.setup()
        await run(prompt_server, address=args.listen, port=args.port, verbose=not args.dont_print_server, call_on_start=call_on_start)

    # Returning these so that other code can integrate with the ComfyUI loop and server
    return asyncio_loop, prompt_server, start_all