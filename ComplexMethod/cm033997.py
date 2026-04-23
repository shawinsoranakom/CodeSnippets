def _init_shm(self) -> dict[str, t.Any]:
        popen_kwargs: dict[str, t.Any] = {}

        if self.get_option('password_mechanism') != 'ssh_askpass':
            return popen_kwargs

        conn_password = self.get_option('password') or self._play_context.password
        pkcs11_provider = self.get_option("pkcs11_provider")
        if not conn_password and pkcs11_provider:
            raise AnsibleError("to use pkcs11_provider you must specify a password/pin")

        if not conn_password:
            return popen_kwargs

        kwargs = {}
        if _HAS_RESOURCE_TRACK:
            # deprecated: description='track argument for SharedMemory always available' python_version='3.12'
            kwargs['track'] = False
        self.shm = shm = SharedMemory(create=True, size=16384, **kwargs)  # type: ignore[arg-type]

        sshpass_prompt = self.get_option('sshpass_prompt')
        if not sshpass_prompt and pkcs11_provider:
            sshpass_prompt = PKCS11_DEFAULT_PROMPT
        elif not sshpass_prompt:
            sshpass_prompt = SSH_ASKPASS_DEFAULT_PROMPT

        data = json.dumps({
            'password': conn_password,
            'prompt': sshpass_prompt,
        }).encode('utf-8')
        shm.buf[:len(data)] = bytearray(data)
        shm.close()

        env = os.environ.copy()
        env['_ANSIBLE_SSH_ASKPASS_SHM'] = str(self.shm.name)
        adhoc = pathlib.Path(sys.argv[0]).with_name('ansible')
        env['SSH_ASKPASS'] = str(adhoc) if adhoc.is_file() else 'ansible'

        # SSH_ASKPASS_REQUIRE was added in openssh 8.4, prior to 8.4 there must be no tty, and DISPLAY must be set
        env['SSH_ASKPASS_REQUIRE'] = 'force'
        if not env.get('DISPLAY'):
            # If the user has DISPLAY set, assume it is there for a reason
            env['DISPLAY'] = '-'

        popen_kwargs['env'] = env
        # start_new_session runs setsid which detaches the tty to support the use of ASKPASS prior to openssh 8.4
        popen_kwargs['start_new_session'] = True

        return popen_kwargs