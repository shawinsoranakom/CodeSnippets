def service_enable_rcconf(self):
        if self.rcconf_file is None or self.rcconf_key is None or self.rcconf_value is None:
            self.module.fail_json(msg="service_enable_rcconf() requires rcconf_file, rcconf_key and rcconf_value")

        self.changed = None
        entry = '%s="%s"\n' % (self.rcconf_key, self.rcconf_value)
        with open(self.rcconf_file, "r") as RCFILE:
            new_rc_conf = []

            # Build a list containing the possibly modified file.
            for rcline in RCFILE:
                # Parse line removing whitespaces, quotes, etc.
                rcarray = shlex.split(rcline, comments=True)
                if len(rcarray) >= 1 and '=' in rcarray[0]:
                    (key, value) = rcarray[0].split("=", 1)
                    if key == self.rcconf_key:
                        if value.upper() == self.rcconf_value:
                            # Since the proper entry already exists we can stop iterating.
                            self.changed = False
                            break
                        else:
                            # We found the key but the value is wrong, replace with new entry.
                            rcline = entry
                            self.changed = True

                # Add line to the list.
                new_rc_conf.append(rcline.strip() + '\n')

        # If we did not see any trace of our entry we need to add it.
        if self.changed is None:
            new_rc_conf.append(entry)
            self.changed = True

        if self.changed is True:

            if self.module.check_mode:
                self.module.exit_json(changed=True, msg="changing service enablement")

            # Create a temporary file next to the current rc.conf (so we stay on the same filesystem).
            # This way the replacement operation is atomic.
            rcconf_dir = os.path.dirname(self.rcconf_file)
            rcconf_base = os.path.basename(self.rcconf_file)
            (TMP_RCCONF, tmp_rcconf_file) = tempfile.mkstemp(dir=rcconf_dir, prefix="%s-" % rcconf_base)

            # Write out the contents of the list into our temporary file.
            for rcline in new_rc_conf:
                os.write(TMP_RCCONF, rcline.encode())

            # Close temporary file.
            os.close(TMP_RCCONF)

            # Replace previous rc.conf.
            self.module.atomic_move(tmp_rcconf_file, self.rcconf_file)