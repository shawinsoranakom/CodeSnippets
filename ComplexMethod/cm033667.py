def apply_defaults(cls, settings: t.Self) -> t.Self:
        if not settings.module:
            if not settings.package or 'pydevd-pycharm' in settings.package:
                module = 'pydevd_pycharm'
            else:
                module = 'pydevd'

            settings = dataclasses.replace(settings, module=module)

        if settings.package is None:
            if settings.module == 'pydevd_pycharm':
                if pycharm_version := detect_pycharm_version():
                    package = f'pydevd-pycharm~={pycharm_version}'
                else:
                    package = None
            else:
                package = 'pydevd'

            settings = dataclasses.replace(settings, package=package)

        settings.settrace.setdefault('suspend', False)

        if port := detect_pydevd_port():
            settings = dataclasses.replace(settings, port=port)

            if detect_pycharm_process():
                # This only works with the default PyCharm debugger.
                # Using it with PyCharm's "Python Debug Server" results in hangs in Ansible workers.
                # Further investigation is required to understand the cause.
                settings = dataclasses.replace(settings, args=settings.args + ['--multiprocess'])

        return settings