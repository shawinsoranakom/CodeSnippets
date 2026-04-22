def start(self) -> None:
        """Start a new thread to process the ScriptEventQueue.

        This must be called only once.

        """
        if self._script_thread is not None:
            raise Exception("ScriptRunner was already started")

        self._script_thread = threading.Thread(
            target=self._run_script_thread,
            name="ScriptRunner.scriptThread",
        )
        self._script_thread.start()