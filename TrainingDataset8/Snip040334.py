def get_app(self):
        server = Server("mock/script/path", "test command line")
        server._runtime.does_script_run_without_error = (
            self.does_script_run_without_error
        )
        server._runtime._eventloop = self.asyncio_loop
        return server._create_app()