def _run_script(self, rerun_data: RerunData) -> None:
        """Run our script.

        Parameters
        ----------
        rerun_data: RerunData
            The RerunData to use.

        """
        assert self._is_in_script_thread()

        _LOGGER.debug("Running script %s", rerun_data)

        start_time: float = timer()
        prep_time: float = 0  # This will be overwritten once preparations are done.

        # Reset DeltaGenerators, widgets, media files.
        runtime.get_instance().media_file_mgr.clear_session_refs()

        main_script_path = self._main_script_path
        pages = source_util.get_pages(main_script_path)
        # Safe because pages will at least contain the app's main page.
        main_page_info = list(pages.values())[0]
        current_page_info = None
        uncaught_exception = None

        if rerun_data.page_script_hash:
            current_page_info = pages.get(rerun_data.page_script_hash, None)
        elif not rerun_data.page_script_hash and rerun_data.page_name:
            # If a user navigates directly to a non-main page of an app, we get
            # the first script run request before the list of pages has been
            # sent to the frontend. In this case, we choose the first script
            # with a name matching the requested page name.
            current_page_info = next(
                filter(
                    # There seems to be this weird bug with mypy where it
                    # thinks that p can be None (which is impossible given the
                    # types of pages), so we add `p and` at the beginning of
                    # the predicate to circumvent this.
                    lambda p: p and (p["page_name"] == rerun_data.page_name),
                    pages.values(),
                ),
                None,
            )
        else:
            # If no information about what page to run is given, default to
            # running the main page.
            current_page_info = main_page_info

        page_script_hash = (
            current_page_info["page_script_hash"]
            if current_page_info is not None
            else main_page_info["page_script_hash"]
        )

        ctx = self._get_script_run_ctx()
        ctx.reset(
            query_string=rerun_data.query_string,
            page_script_hash=page_script_hash,
        )

        self.on_event.send(
            self,
            event=ScriptRunnerEvent.SCRIPT_STARTED,
            page_script_hash=page_script_hash,
        )

        # Compile the script. Any errors thrown here will be surfaced
        # to the user via a modal dialog in the frontend, and won't result
        # in their previous script elements disappearing.
        try:
            if current_page_info:
                script_path = current_page_info["script_path"]
            else:
                script_path = main_script_path

                # At this point, we know that either
                #   * the script corresponding to the hash requested no longer
                #     exists, or
                #   * we were not able to find a script with the requested page
                #     name.
                # In both of these cases, we want to send a page_not_found
                # message to the frontend.
                msg = ForwardMsg()
                msg.page_not_found.page_name = rerun_data.page_name
                ctx.enqueue(msg)

            with source_util.open_python_file(script_path) as f:
                filebody = f.read()

            if config.get_option("runner.magicEnabled"):
                filebody = magic.add_magic(filebody, script_path)

            code = compile(
                filebody,
                # Pass in the file path so it can show up in exceptions.
                script_path,
                # We're compiling entire blocks of Python, so we need "exec"
                # mode (as opposed to "eval" or "single").
                mode="exec",
                # Don't inherit any flags or "future" statements.
                flags=0,
                dont_inherit=1,
                # Use the default optimization options.
                optimize=-1,
            )

        except Exception as ex:
            # We got a compile error. Send an error event and bail immediately.
            _LOGGER.debug("Fatal script error: %s", ex)
            self._session_state[SCRIPT_RUN_WITHOUT_ERRORS_KEY] = False
            self.on_event.send(
                self,
                event=ScriptRunnerEvent.SCRIPT_STOPPED_WITH_COMPILE_ERROR,
                exception=ex,
            )
            return

        # If we get here, we've successfully compiled our script. The next step
        # is to run it. Errors thrown during execution will be shown to the
        # user as ExceptionElements.

        if config.get_option("runner.installTracer"):
            self._install_tracer()

        # This will be set to a RerunData instance if our execution
        # is interrupted by a RerunException.
        rerun_exception_data: Optional[RerunData] = None

        try:
            # Create fake module. This gives us a name global namespace to
            # execute the code in.
            # TODO(vdonato): Double-check that we're okay with naming the
            # module for every page `__main__`. I'm pretty sure this is
            # necessary given that people will likely often write
            #     ```
            #     if __name__ == "__main__":
            #         ...
            #     ```
            # in their scripts.
            module = _new_module("__main__")

            # Install the fake module as the __main__ module. This allows
            # the pickle module to work inside the user's code, since it now
            # can know the module where the pickled objects stem from.
            # IMPORTANT: This means we can't use "if __name__ == '__main__'" in
            # our code, as it will point to the wrong module!!!
            sys.modules["__main__"] = module

            # Add special variables to the module's globals dict.
            # Note: The following is a requirement for the CodeHasher to
            # work correctly. The CodeHasher is scoped to
            # files contained in the directory of __main__.__file__, which we
            # assume is the main script directory.
            module.__dict__["__file__"] = script_path

            with modified_sys_path(self._main_script_path), self._set_execing_flag():
                # Run callbacks for widgets whose values have changed.
                if rerun_data.widget_states is not None:
                    self._session_state.on_script_will_rerun(rerun_data.widget_states)

                ctx.on_script_start()
                prep_time = timer() - start_time
                exec(code, module.__dict__)
                self._session_state[SCRIPT_RUN_WITHOUT_ERRORS_KEY] = True
        except RerunException as e:
            rerun_exception_data = e.rerun_data

        except StopException:
            # This is thrown when the script executes `st.stop()`.
            # We don't have to do anything here.
            pass

        except Exception as ex:
            self._session_state[SCRIPT_RUN_WITHOUT_ERRORS_KEY] = False
            uncaught_exception = ex
            handle_uncaught_app_exception(uncaught_exception)

        finally:
            if rerun_exception_data:
                finished_event = ScriptRunnerEvent.SCRIPT_STOPPED_FOR_RERUN
            else:
                finished_event = ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS

            if ctx.gather_usage_stats:
                try:
                    # Prevent issues with circular import
                    from streamlit.runtime.metrics_util import (
                        create_page_profile_message,
                        to_microseconds,
                    )

                    # Create and send page profile information
                    ctx.enqueue(
                        create_page_profile_message(
                            ctx.tracked_commands,
                            exec_time=to_microseconds(timer() - start_time),
                            prep_time=to_microseconds(prep_time),
                            uncaught_exception=type(uncaught_exception).__name__
                            if uncaught_exception
                            else None,
                        )
                    )
                except Exception as ex:
                    # Always capture all exceptions since we want to make sure that
                    # the telemetry never causes any issues.
                    _LOGGER.debug("Failed to create page profile", exc_info=ex)
            self._on_script_finished(ctx, finished_event)

        # Use _log_if_error() to make sure we never ever ever stop running the
        # script without meaning to.
        _log_if_error(_clean_problem_modules)

        if rerun_exception_data is not None:
            self._run_script(rerun_exception_data)