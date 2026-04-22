def _on_script_finished(
        self, ctx: ScriptRunContext, event: ScriptRunnerEvent
    ) -> None:
        """Called when our script finishes executing, even if it finished
        early with an exception. We perform post-run cleanup here.
        """
        # Tell session_state to update itself in response
        self._session_state.on_script_finished(ctx.widget_ids_this_run)

        # Signal that the script has finished. (We use SCRIPT_STOPPED_WITH_SUCCESS
        # even if we were stopped with an exception.)
        self.on_event.send(self, event=event)

        # Remove orphaned files now that the script has run and files in use
        # are marked as active.
        runtime.get_instance().media_file_mgr.remove_orphaned_files()

        # Force garbage collection to run, to help avoid memory use building up
        # This is usually not an issue, but sometimes GC takes time to kick in and
        # causes apps to go over resource limits, and forcing it to run between
        # script runs is low cost, since we aren't doing much work anyway.
        if config.get_option("runner.postScriptGC"):
            gc.collect(2)