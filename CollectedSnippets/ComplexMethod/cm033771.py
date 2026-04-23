def test_python_module(path, name, base_dir, messages, restrict_to_module_paths):
        """Test the given python module by importing it.
        :type path: str
        :type name: str
        :type base_dir: str
        :type messages: set[str]
        :type restrict_to_module_paths: bool
        """
        if name in sys.modules:
            return  # cannot be tested because it has already been loaded

        is_ansible_module = (path.startswith('lib/ansible/modules/') or path.startswith('plugins/modules/')) and os.path.basename(path) != '__init__.py'
        run_main = is_ansible_module

        if path == 'lib/ansible/modules/async_wrapper.py':
            # async_wrapper is a non-standard Ansible module (does not use AnsibleModule) so we cannot test the main function
            run_main = False

        capture_normal = Capture()
        capture_main = Capture()

        run_module_ok = False

        try:
            with monitor_sys_modules(path, messages):
                with restrict_imports(path, name, messages, restrict_to_module_paths):
                    with capture_output(capture_normal):
                        import_module(name)

            if run_main:
                run_module_ok = is_ansible_module

                with monitor_sys_modules(path, messages):
                    with restrict_imports(path, name, messages, restrict_to_module_paths):
                        with capture_output(capture_main):
                            runpy.run_module(name, run_name='__main__', alter_sys=True)
        except ImporterAnsibleModuleException:
            # module instantiated AnsibleModule without raising an exception
            if not run_module_ok:
                if is_ansible_module:
                    report_message(path, 0, 0, 'module-guard', "AnsibleModule instantiation not guarded by `if __name__ == '__main__'`", messages)
                else:
                    report_message(path, 0, 0, 'non-module', "AnsibleModule instantiated by import of non-module", messages)
        except BaseException as ex:  # pylint: disable=locally-disabled, broad-except
            # intentionally catch all exceptions, including calls to sys.exit
            exc_type, _exc, exc_tb = sys.exc_info()
            message = str(ex)
            results = list(reversed(traceback.extract_tb(exc_tb)))
            line = 0
            offset = 0
            full_path = os.path.join(base_dir, path)
            base_path = base_dir + os.path.sep
            source = None

            # avoid line wraps in messages
            message = re.sub(r'\n *', ': ', message)

            for result in results:
                if result[0] == full_path:
                    # save the line number for the file under test
                    line = result[1] or 0

                if not source and result[0].startswith(base_path) and not result[0].startswith(temp_path):
                    # save the first path and line number in the traceback which is in our source tree
                    source = (os.path.relpath(result[0], base_path), result[1] or 0, 0)

            if isinstance(ex, SyntaxError):
                # SyntaxError has better information than the traceback
                if ex.filename == full_path:  # pylint: disable=locally-disabled, no-member
                    # syntax error was reported in the file under test
                    line = ex.lineno or 0  # pylint: disable=locally-disabled, no-member
                    offset = ex.offset or 0  # pylint: disable=locally-disabled, no-member
                elif ex.filename.startswith(base_path) and not ex.filename.startswith(temp_path):  # pylint: disable=locally-disabled, no-member
                    # syntax error was reported in our source tree
                    source = (os.path.relpath(ex.filename, base_path), ex.lineno or 0, ex.offset or 0)  # pylint: disable=locally-disabled, no-member

                # remove the filename and line number from the message
                # either it was extracted above, or it's not really useful information
                message = re.sub(r' \(.*?, line [0-9]+\)$', '', message)

            if source and source[0] != path:
                message += ' (at %s:%d:%d)' % (source[0], source[1], source[2])

            report_message(path, line, offset, 'traceback', '%s: %s' % (exc_type.__name__, message), messages)
        finally:
            capture_report(path, capture_normal, messages)
            capture_report(path, capture_main, messages)