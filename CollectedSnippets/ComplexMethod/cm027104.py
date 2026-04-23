def _run(self) -> None:
        """Start processing events to save."""
        thread_id = threading.get_ident()
        self.thread_id = thread_id
        self.recorder_and_worker_thread_ids.add(thread_id)

        setup_result = self._setup_recorder()

        if not setup_result:
            _LOGGER.error("Recorder setup failed, recorder shutting down")
            # Give up if we could not connect
            return

        schema_status = migration.validate_db_schema(self.hass, self, self.get_session)
        if schema_status is None:
            # Give up if we could not validate the schema
            _LOGGER.error("Failed to validate schema, recorder shutting down")
            return
        if schema_status.current_version > SCHEMA_VERSION:
            _LOGGER.error(
                "The database schema version %s is newer than %s which is the maximum "
                "database schema version supported by the installed version of "
                "Home Assistant Core, either upgrade Home Assistant Core or restore "
                "the database from a backup compatible with this version",
                schema_status.current_version,
                SCHEMA_VERSION,
            )
            return
        self.schema_version = schema_status.current_version

        if not schema_status.migration_needed and not schema_status.schema_errors:
            self._setup_run()
        else:
            self.migration_in_progress = True
            self.migration_is_live = migration.live_migration(schema_status)

        self.hass.add_job(self.async_connection_success)

        # First do non-live migration steps, if needed
        if schema_status.migration_needed:
            # Do non-live schema migration
            result, schema_status = self._migrate_schema_offline(schema_status)
            if not result:
                self._notify_migration_failed()
                self.migration_in_progress = False
                return
            self.schema_version = schema_status.current_version

            # Do non-live data migration
            self._migrate_data_offline(schema_status)

            # Non-live migration is now completed, remaining steps are live
            self.migration_is_live = True

        # After non-live migration, activate the recorder
        self._activate_and_set_db_ready(schema_status)
        # We wait to start a live migration until startup has finished
        # since it can be cpu intensive and we do not want it to compete
        # with startup which is also cpu intensive
        if self._wait_startup_or_shutdown() is SHUTDOWN_TASK:
            # Shutdown happened before Home Assistant finished starting
            self.migration_in_progress = False
            # Make sure we cleanly close the run if
            # we restart before startup finishes
            return

        # Do live migration steps and repairs, if needed
        if schema_status.migration_needed or schema_status.schema_errors:
            result, schema_status = self._migrate_schema_live(schema_status)
            if result:
                self.schema_version = SCHEMA_VERSION
                if not self._event_listener:
                    # If the schema migration takes so long that the end
                    # queue watcher safety kicks in because _reached_max_backlog
                    # was True, we need to reinitialize the listener.
                    self.hass.add_job(self.async_initialize)
            else:
                self.migration_in_progress = False
                self._dismiss_migration_in_progress()
                self._notify_migration_failed()
                return

        # Schema migration and repair is now completed
        if self.migration_in_progress:
            self.migration_in_progress = False
            self._dismiss_migration_in_progress()
            self._setup_run()

        # Catch up with missed statistics
        self._schedule_compile_missing_statistics()

        # Kick off live migrations
        migration.migrate_data_live(self, self.get_session, schema_status)

        _LOGGER.debug("Recorder processing the queue")
        self._adjust_lru_size()
        self.hass.add_job(self._async_set_recorder_ready_migration_done)
        self._run_event_loop()