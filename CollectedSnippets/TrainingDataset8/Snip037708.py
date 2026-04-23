def shutdown(self) -> None:
        """Shut down the AppSession.

        It's an error to use a AppSession after it's been shut down.

        """
        if self._state != AppSessionState.SHUTDOWN_REQUESTED:
            LOGGER.debug("Shutting down (id=%s)", self.id)
            # Clear any unused session files in upload file manager and media
            # file manager
            self._uploaded_file_mgr.remove_session_files(self.id)
            runtime.get_instance().media_file_mgr.clear_session_refs(self.id)
            runtime.get_instance().media_file_mgr.remove_orphaned_files()

            # Shut down the ScriptRunner, if one is active.
            # self._state must not be set to SHUTDOWN_REQUESTED until
            # after this is called.
            if self._scriptrunner is not None:
                self._scriptrunner.request_stop()

            self._state = AppSessionState.SHUTDOWN_REQUESTED
            self._local_sources_watcher.close()
            if self._stop_config_listener is not None:
                self._stop_config_listener()
            if self._stop_pages_listener is not None:
                self._stop_pages_listener()
            secrets_singleton._file_change_listener.disconnect(
                self._on_secrets_file_changed
            )