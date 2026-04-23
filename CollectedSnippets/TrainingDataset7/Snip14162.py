def run(self, django_main_thread):
        global _url_module_exception
        logger.debug("Waiting for apps ready_event.")
        self.wait_for_apps_ready(apps, django_main_thread)
        from django.urls import get_resolver

        # Prevent a race condition where URL modules aren't loaded when the
        # reloader starts by accessing the urlconf_module property.
        try:
            get_resolver().urlconf_module
        except Exception as e:
            # Loading the urlconf can result in errors during development.
            # If this occurs then store the error and continue.
            _url_module_exception = e
        logger.debug("Apps ready_event triggered. Sending autoreload_started signal.")
        autoreload_started.send(sender=self)
        self.run_loop()