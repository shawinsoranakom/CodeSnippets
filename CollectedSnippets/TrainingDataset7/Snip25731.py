def patch_django_server_logger():
            old_stream = logger.handlers[0].stream
            new_stream = StringIO()
            logger.handlers[0].stream = new_stream
            yield new_stream
            logger.handlers[0].stream = old_stream