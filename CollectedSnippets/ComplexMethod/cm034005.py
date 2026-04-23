def _parse_pipeline_result(self, pipeline: PowerShell) -> tuple[int, bytes, bytes]:
        """
        PSRP doesn't have the same concept as other protocols with its output.
        We need some extra logic to convert the pipeline streams and host
        output into the format that Ansible understands.

        :param pipeline: The finished PowerShell pipeline that invoked our
            commands
        :return: rc, stdout, stderr based on the pipeline output
        """
        # we try and get the rc from our host implementation, this is set if
        # exit or $host.SetShouldExit() is called in our pipeline, if not we
        # set to 0 if the pipeline had not errors and 1 if it did
        rc = self.host.rc or (1 if pipeline.had_errors else 0)

        # TODO: figure out a better way of merging this with the host output
        stdout_list = []
        for output in pipeline.output:
            # Not all pipeline outputs are a string or contain a __str__ value,
            # we will create our own output based on the properties of the
            # complex object if that is the case.
            if isinstance(output, GenericComplexObject) and output.to_string is None:
                obj_lines = output.property_sets
                for key, value in output.adapted_properties.items():
                    obj_lines.append(u"%s: %s" % (key, value))
                for key, value in output.extended_properties.items():
                    obj_lines.append(u"%s: %s" % (key, value))
                output_msg = u"\n".join(obj_lines)
            else:
                output_msg = to_text(output, nonstring='simplerepr')

            stdout_list.append(output_msg)

        if len(self.host.ui.stdout) > 0:
            stdout_list += self.host.ui.stdout
        stdout = u"\r\n".join(stdout_list)

        stderr_list = []
        for error in pipeline.streams.error:
            # the error record is not as fully fleshed out like we usually get
            # in PS, we will manually create it here
            # NativeCommandError and NativeCommandErrorMessage are special
            # cases used for stderr from a subprocess, we will just print the
            # error message
            if error.fq_error in ['NativeCommandError', 'NativeCommandErrorMessage']:
                stderr_list.append(f"{error}\r\n")
                continue

            command_name = "%s : " % error.command_name if error.command_name else ''
            position = "%s\r\n" % error.invocation_position_message if error.invocation_position_message else ''
            error_msg = "%s%s\r\n%s" \
                        "    + CategoryInfo          : %s\r\n" \
                        "    + FullyQualifiedErrorId : %s" \
                        % (command_name, str(error), position,
                           error.message, error.fq_error)
            stacktrace = error.script_stacktrace
            if display.verbosity >= 3 and stacktrace is not None:
                error_msg += "\r\nStackTrace:\r\n%s" % stacktrace
            stderr_list.append(f"{error_msg}\r\n")

        if len(self.host.ui.stderr) > 0:
            stderr_list += self.host.ui.stderr
        stderr = "".join([to_text(o) for o in stderr_list])

        display.vvvvv("PSRP RC: %d" % rc, host=self._psrp_host)
        display.vvvvv("PSRP STDOUT: %s" % stdout, host=self._psrp_host)
        display.vvvvv("PSRP STDERR: %s" % stderr, host=self._psrp_host)

        # reset the host back output back to defaults, needed if running
        # multiple pipelines on the same RunspacePool
        self.host.rc = 0
        self.host.ui.stdout = []
        self.host.ui.stderr = []

        return rc, to_bytes(stdout, encoding='utf-8'), to_bytes(stderr, encoding='utf-8')