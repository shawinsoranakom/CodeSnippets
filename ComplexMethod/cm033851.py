def send_callback(self, method_name, *args, **kwargs):
        # We always send events to stdout callback first, rest should follow config order
        for callback_plugin in self._callback_plugins:
            # a plugin that set self.disabled to True will not be called
            # see osx_say.py example for such a plugin
            if callback_plugin.disabled:
                continue

            # a plugin can opt in to implicit tasks (such as meta). It does this
            # by declaring self.wants_implicit_tasks = True.
            if not callback_plugin.wants_implicit_tasks and (task_arg := self._first_arg_of_type(Task, args)) and task_arg.implicit:
                continue

            methods = []

            if method_name in callback_plugin._implemented_callback_methods:
                methods.append(getattr(callback_plugin, method_name))

            if 'v2_on_any' in callback_plugin._implemented_callback_methods:
                methods.append(getattr(callback_plugin, 'v2_on_any'))

            for method in methods:
                # send clean copies
                new_args = []

                for arg in args:
                    # FIXME: add play/task cleaners
                    if isinstance(arg, HostTaskResult):
                        copied_tr = CallbackTaskResult(host=arg.host, task=arg.task, utr=arg.utr)
                        new_args.append(copied_tr)
                        # this state hack requires that no callback ever accepts > 1 TaskResult object
                        callback_plugin._current_task_result = copied_tr
                    else:
                        new_args.append(arg)

                with self._callback_dispatch_error_handler.handle(AnsibleCallbackError):
                    try:
                        method(*new_args, **kwargs)
                    except AssertionError:
                        # Using an `assert` in integration tests is useful.
                        # Production code should never use `assert` or raise `AssertionError`.
                        raise
                    except Exception as ex:
                        raise AnsibleCallbackError(f"Callback dispatch {method_name!r} failed for plugin {callback_plugin._load_name!r}.") from ex

            callback_plugin._current_task_result = None