def on_script_finished(self, widget_ids_this_run: Set[str]) -> None:
        """Called by ScriptRunner after its script finishes running.
         Updates widgets to prepare for the next script run.

        Parameters
        ----------
        widget_ids_this_run: Set[str]
            The IDs of the widgets that were accessed during the script
            run. Any widget whose ID does *not* appear in this set will
            be culled.
        """
        self._reset_triggers()
        self._cull_nonexistent(widget_ids_this_run)