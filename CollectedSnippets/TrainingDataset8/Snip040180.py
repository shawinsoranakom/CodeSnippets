def test_script_and_2_modules_in_series(self, fob):
        lso = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lso.register_file_change_callback(NOOP_CALLBACK)

        fob.assert_called_once()

        sys.modules["DUMMY_MODULE_1"] = DUMMY_MODULE_1
        fob.reset_mock()

        lso.update_watched_modules()

        self.assertEqual(fob.call_count, 2)  # dummy module and __init__.py

        method_type = type(self.setUp)

        call_args_list = sort_args_list(fob.call_args_list)

        args, _ = call_args_list[0]
        self.assertIn("__init__.py", args[0])

        args, _ = call_args_list[1]
        self.assertEqual(args[0], DUMMY_MODULE_1_FILE)
        self.assertEqual(type(args[1]), method_type)

        sys.modules["DUMMY_MODULE_2"] = DUMMY_MODULE_2
        fob.reset_mock()
        lso.update_watched_modules()

        args, _ = fob.call_args
        self.assertEqual(args[0], DUMMY_MODULE_2_FILE)
        self.assertEqual(type(args[1]), method_type)

        fob.assert_called_once()