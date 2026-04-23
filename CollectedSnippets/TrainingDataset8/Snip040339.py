def get_app(self):
        server = Server("mock/script/path", "test command line")
        server.does_script_run_without_error = self.does_script_run_without_error
        return server._create_app()