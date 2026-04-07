def save(self, must_create=False):
        if self.session_key is None:
            return self.create()
        # Get the session data now, before we start messing
        # with the file it is stored within.
        session_data = self._get_session(no_load=must_create)

        session_file_name = self._key_to_file()

        try:
            # Make sure the file exists. If it does not already exist, an
            # empty placeholder file is created.
            flags = os.O_WRONLY | getattr(os, "O_BINARY", 0)
            if must_create:
                flags |= os.O_EXCL | os.O_CREAT
            fd = os.open(session_file_name, flags)
            os.close(fd)
        except FileNotFoundError:
            if not must_create:
                raise UpdateError
        except FileExistsError:
            if must_create:
                raise CreateError

        # Write the session file without interfering with other threads
        # or processes. By writing to an atomically generated temporary
        # file and then using the atomic os.rename() to make the complete
        # file visible, we avoid having to lock the session file, while
        # still maintaining its integrity.
        #
        # Note: Locking the session file was explored, but rejected in part
        # because in order to be atomic and cross-platform, it required a
        # long-lived lock file for each session, doubling the number of
        # files in the session storage directory at any given time. This
        # rename solution is cleaner and avoids any additional overhead
        # when reading the session data, which is the more common case
        # unless SESSION_SAVE_EVERY_REQUEST = True.
        #
        # See ticket #8616.
        dir, prefix = os.path.split(session_file_name)

        try:
            output_file_fd, output_file_name = tempfile.mkstemp(
                dir=dir, prefix=prefix + "_out_"
            )
            renamed = False
            try:
                try:
                    os.write(output_file_fd, self.encode(session_data).encode())
                finally:
                    os.close(output_file_fd)

                # This will atomically rename the file (os.rename) if the OS
                # supports it. Otherwise this will result in a shutil.copy2
                # and os.unlink (for example on Windows). See #9084.
                shutil.move(output_file_name, session_file_name)
                renamed = True
            finally:
                if not renamed:
                    os.unlink(output_file_name)
        except (EOFError, OSError):
            pass