def log(self, msg, log_args=None):

        if not self.no_log:

            if log_args is None:
                log_args = dict()

            module = 'ansible-%s' % self._name
            if isinstance(module, bytes):
                module = module.decode('utf-8', 'replace')

            # 6655 - allow for accented characters
            if not isinstance(msg, (bytes, str)):
                raise TypeError("msg should be a string (got %s)" % type(msg))

            # We want journal to always take text type
            # syslog takes bytes on py2, text type on py3
            if isinstance(msg, bytes):
                journal_msg = msg.decode('utf-8', 'replace')
            else:
                # TODO: surrogateescape is a danger here on Py3
                journal_msg = msg

            if self._target_log_info:
                journal_msg = ' '.join([self._target_log_info, journal_msg])

            # ensure we clean up secrets!
            journal_msg = remove_values(journal_msg, self.no_log_values)

            if has_journal:
                journal_args = [("MODULE", os.path.basename(__file__))]
                for arg in log_args:
                    name, value = (arg.upper(), str(log_args[arg]))
                    if name in (
                        'PRIORITY', 'MESSAGE', 'MESSAGE_ID',
                        'CODE_FILE', 'CODE_LINE', 'CODE_FUNC',
                        'SYSLOG_FACILITY', 'SYSLOG_IDENTIFIER',
                        'SYSLOG_PID',
                    ):
                        name = "_%s" % name
                    journal_args.append((name, value))

                try:
                    if HAS_SYSLOG:
                        # If syslog_facility specified, it needs to convert
                        #  from the facility name to the facility code, and
                        #  set it as SYSLOG_FACILITY argument of journal.send()
                        facility = getattr(syslog,
                                           self._syslog_facility,
                                           syslog.LOG_USER) >> 3
                        journal.send(MESSAGE=u"%s %s" % (module, journal_msg),
                                     SYSLOG_FACILITY=facility,
                                     **dict(journal_args))
                    else:
                        journal.send(MESSAGE=u"%s %s" % (module, journal_msg),
                                     **dict(journal_args))
                except OSError:
                    # fall back to syslog since logging to journal failed
                    self._log_to_syslog(journal_msg)
            else:
                self._log_to_syslog(journal_msg)