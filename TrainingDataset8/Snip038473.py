def tearDown(self):
        self.clear_queue()
        add_script_run_ctx(threading.current_thread(), self.orig_report_ctx)
        Runtime._instance = None