def atomic_move(self, src, dest, unsafe_writes=False, keep_dest_attrs=True):
        """atomically move src to dest, copying attributes from dest, returns true on success
        it uses os.rename to ensure this as it is an atomic operation, rest of the function is
        to work around limitations, corner cases and ensure selinux context is saved if possible"""
        context = None
        dest_stat = None
        b_src = to_bytes(src, errors='surrogate_or_strict')
        b_dest = to_bytes(dest, errors='surrogate_or_strict')
        if os.path.exists(b_dest) and keep_dest_attrs:
            try:
                dest_stat = os.stat(b_dest)
                os.chown(b_src, dest_stat.st_uid, dest_stat.st_gid)
                shutil.copystat(b_dest, b_src)
                os.utime(b_src, times=(time.time(), time.time()))
            except OSError as e:
                if e.errno != errno.EPERM:
                    raise
            if self.selinux_enabled():
                context = self.selinux_context(dest)
        else:
            if self.selinux_enabled():
                context = self.selinux_default_context(dest)

        creating = not os.path.exists(b_dest)

        try:
            # Optimistically try a rename, solves some corner cases and can avoid useless work, throws exception if not atomic.
            os.rename(b_src, b_dest)
        except OSError as ex:
            if ex.errno in (errno.EPERM, errno.EXDEV, errno.EACCES, errno.ETXTBSY, errno.EBUSY):
                # only try workarounds for errno 18 (cross device), 1 (not permitted),  13 (permission denied)
                # and 26 (text file busy) which happens on vagrant synced folders and other 'exotic' non posix file systems
                # Use bytes here.  In the shippable CI, this fails with
                # a UnicodeError with surrogateescape'd strings for an unknown
                # reason (doesn't happen in a local Ubuntu16.04 VM)
                b_dest_dir = os.path.dirname(b_dest)
                b_suffix = os.path.basename(b_dest)
                tmp_dest_name = None
                try:
                    tmp_dest_fd, tmp_dest_name = tempfile.mkstemp(prefix=b'.ansible_tmp', dir=b_dest_dir, suffix=b_suffix)
                except OSError as ex:
                    if unsafe_writes:
                        self._unsafe_writes(b_src, b_dest)
                    else:
                        raise Exception(
                            f'The destination directory {os.path.dirname(dest)!r} is not writable by the current user.'
                        ) from ex

                if tmp_dest_name:
                    b_tmp_dest_name = to_bytes(tmp_dest_name, errors='surrogate_or_strict')

                    try:
                        try:
                            # close tmp file handle before file operations to prevent text file busy errors on vboxfs synced folders (windows host)
                            os.close(tmp_dest_fd)
                            # leaves tmp file behind when sudo and not root
                            try:
                                shutil.move(b_src, b_tmp_dest_name, copy_function=shutil.copy if keep_dest_attrs else shutil.copy2)
                            except OSError:
                                # cleanup will happen by 'rm' of tmpdir
                                # copy2 will preserve some metadata
                                if keep_dest_attrs:
                                    shutil.copy(b_src, b_tmp_dest_name)
                                else:
                                    shutil.copy2(b_src, b_tmp_dest_name)

                            if self.selinux_enabled():
                                self.set_context_if_different(
                                    b_tmp_dest_name, context, False)
                            try:
                                tmp_stat = os.stat(b_tmp_dest_name)
                                if keep_dest_attrs:
                                    if dest_stat and (tmp_stat.st_uid != dest_stat.st_uid or tmp_stat.st_gid != dest_stat.st_gid):
                                        os.chown(b_tmp_dest_name, dest_stat.st_uid, dest_stat.st_gid)
                                    os.utime(b_tmp_dest_name, times=(time.time(), time.time()))
                            except OSError as ex:
                                if ex.errno != errno.EPERM:
                                    raise
                            try:
                                os.rename(b_tmp_dest_name, b_dest)
                            except (shutil.Error, OSError) as ex:
                                if unsafe_writes and ex.errno == errno.EBUSY:
                                    self._unsafe_writes(b_tmp_dest_name, b_dest)
                                else:
                                    raise Exception(
                                        f'Unable to make {src!r} into to {dest!r}, failed final rename from {to_text(b_tmp_dest_name)!r}.'
                                    ) from ex
                        except (shutil.Error, OSError) as ex:
                            if unsafe_writes:
                                self._unsafe_writes(b_src, b_dest)
                            else:
                                raise Exception(f'Failed to replace {dest!r} with {src!r}.') from ex
                    finally:
                        self.cleanup(b_tmp_dest_name)
            else:
                raise Exception(f'Could not replace {dest!r} with {src!r}.') from ex

        if creating:
            # make sure the file has the correct permissions
            # based on the current value of umask
            umask = os.umask(0)
            os.umask(umask)
            os.chmod(b_dest, S_IRWU_RWG_RWO & ~umask)
            dest_dir_stat = os.stat(os.path.dirname(b_dest))
            try:
                if dest_dir_stat.st_mode & stat.S_ISGID:
                    os.chown(b_dest, os.geteuid(), dest_dir_stat.st_gid)
                else:
                    os.chown(b_dest, os.geteuid(), os.getegid())
            except OSError:
                # We're okay with trying our best here.  If the user is not
                # root (or old Unices) they won't be able to chown.
                pass

        if self.selinux_enabled():
            # rename might not preserve context
            self.set_context_if_different(dest, context, False)