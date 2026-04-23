def get_py_argument_spec(filename, collection):
    name = get_module_name_from_filename(filename, collection)

    with setup_env(filename) as fake:
        try:
            with CaptureStd():
                runpy.run_module(name, run_name='__main__', alter_sys=True)
        except AnsibleModuleCallError:
            pass
        except BaseException as e:
            # we want to catch all exceptions here, including sys.exit
            raise AnsibleModuleImportError from e

        if not fake.called:
            raise AnsibleModuleNotInitialized()

    try:
        # Convert positional arguments to kwargs to make sure that all parameters are actually checked
        for arg, arg_name in zip(fake.args, ANSIBLE_MODULE_CONSTRUCTOR_ARGS):
            fake.kwargs[arg_name] = arg
        # for ping kwargs == {'argument_spec':{'data':{'type':'str','default':'pong'}}, 'supports_check_mode':True}
        argument_spec = fake.kwargs.get('argument_spec') or {}
        # If add_file_common_args is truish, add options from FILE_COMMON_ARGUMENTS when not present.
        # This is the only modification to argument_spec done by AnsibleModule itself, and which is
        # not caught by setup_env's AnsibleModule replacement
        if fake.kwargs.get('add_file_common_args'):
            for k, v in FILE_COMMON_ARGUMENTS.items():
                if k not in argument_spec:
                    argument_spec[k] = v
        return argument_spec, fake.kwargs
    except (TypeError, IndexError):
        return {}, {}