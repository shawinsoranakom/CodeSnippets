def write_data(self, data, thefile, shred=True, mode=0o600):
        # TODO: add docstrings for arg types since this code is picky about that
        """Write the data bytes to given path

        This is used to write a byte string to a file or stdout. It is used for
        writing the results of vault encryption or decryption. It is used for
        saving the ciphertext after encryption and it is also used for saving the
        plaintext after decrypting a vault. The type of the 'data' arg should be bytes,
        since in the plaintext case, the original contents can be of any text encoding
        or arbitrary binary data.

        When used to write the result of vault encryption, the value of the 'data' arg
        should be a utf-8 encoded byte string and not a text type.

        When used to write the result of vault decryption, the value of the 'data' arg
        should be a byte string and not a text type.

        :arg data: the byte string (bytes) data
        :arg thefile: file descriptor or filename to save 'data' to.
        :arg shred: if shred==True, make sure that the original data is first shredded so that is cannot be recovered.
        :returns: None
        """
        # FIXME: do we need this now? data_bytes should always be a utf-8 byte string
        b_file_data = to_bytes(data, errors='strict')

        # check if we have a file descriptor instead of a path
        is_fd = False
        try:
            is_fd = (isinstance(thefile, int) and fcntl.fcntl(thefile, fcntl.F_GETFD) != -1)
        except Exception:
            pass

        if is_fd:
            # if passed descriptor, use that to ensure secure access, otherwise it is a string.
            # assumes the fd is securely opened by caller (mkstemp)
            os.ftruncate(thefile, 0)
            os.write(thefile, b_file_data)
        elif thefile == '-':
            # get a ref to either sys.stdout.buffer for py3 or plain old sys.stdout for py2
            # We need sys.stdout.buffer on py3 so we can write bytes to it since the plaintext
            # of the vaulted object could be anything/binary/etc
            output = getattr(sys.stdout, 'buffer', sys.stdout)
            output.write(b_file_data)
        else:
            if not os.access(os.path.dirname(thefile), os.W_OK):
                raise AnsibleError("Destination '%s' not writable" % (os.path.dirname(thefile)))
            # file names are insecure and prone to race conditions, so remove and create securely
            if os.path.isfile(thefile):
                if shred:
                    self._shred_file(thefile)
                else:
                    os.remove(thefile)

            # when setting new umask, we get previous as return
            current_umask = os.umask(0o077)
            try:
                try:
                    # create file with secure permissions
                    fd = os.open(thefile, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_TRUNC, mode)
                except FileExistsError as ex:
                    raise AnsibleError('Vault file got recreated while we were operating on it.') from ex
                except OSError as ex:
                    raise AnsibleError('Problem creating temporary vault file.') from ex

                try:
                    # now write to the file and ensure ours is only data in it
                    os.ftruncate(fd, 0)
                    os.write(fd, b_file_data)
                except OSError as e:
                    raise AnsibleError('Unable to write to temporary vault file: %s' % to_native(e))
                finally:
                    # Make sure the file descriptor is always closed and reset umask
                    os.close(fd)
            finally:
                os.umask(current_umask)