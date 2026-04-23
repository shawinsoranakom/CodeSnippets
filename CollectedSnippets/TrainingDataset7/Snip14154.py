def start_django(reloader, main_func, *args, **kwargs):
    ensure_echo_on()

    main_func = check_errors(main_func)
    django_main_thread = threading.Thread(
        target=main_func, args=args, kwargs=kwargs, name="django-main-thread"
    )
    django_main_thread.daemon = True
    django_main_thread.start()

    while not reloader.should_stop:
        reloader.run(django_main_thread)