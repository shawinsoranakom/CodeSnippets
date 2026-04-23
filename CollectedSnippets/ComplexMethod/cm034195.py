def get_password_from_file(pwd_file: str) -> str:
        b_pwd_file = to_bytes(pwd_file)

        if b_pwd_file == b'-':
            # ensure its read as bytes
            secret = sys.stdin.buffer.read()

        elif not os.path.exists(b_pwd_file):
            raise AnsibleError("The password file %s was not found" % pwd_file)

        elif is_executable(b_pwd_file):
            display.vvvv(u'The password file %s is a script.' % to_text(pwd_file))
            cmd = [b_pwd_file]

            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as e:
                raise AnsibleError("Problem occurred when trying to run the password script %s (%s)."
                                   " If this is not a script, remove the executable bit from the file." % (pwd_file, e))

            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise AnsibleError("The password script %s returned an error (rc=%s): %s" % (pwd_file, p.returncode, to_text(stderr)))
            secret = stdout

        else:
            try:
                with open(b_pwd_file, "rb") as password_file:
                    secret = password_file.read().strip()
            except OSError as ex:
                raise AnsibleError(f"Could not read password file {pwd_file!r}.") from ex

        secret = secret.strip(b'\r\n')

        if not secret:
            raise AnsibleError('Empty password was provided from file (%s)' % pwd_file)

        return to_text(secret)