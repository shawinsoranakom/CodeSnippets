def _clone_db(self, source_database_name, target_database_name):
        cmd_args, cmd_env = DatabaseClient.settings_to_cmd_args_env(
            self.connection.settings_dict, []
        )
        dump_cmd = [
            "mysqldump",
            *cmd_args[1:-1],
            "--routines",
            "--events",
            source_database_name,
        ]
        dump_env = load_env = {**os.environ, **cmd_env} if cmd_env else None
        load_cmd = cmd_args
        load_cmd[-1] = target_database_name

        with (
            subprocess.Popen(
                dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dump_env
            ) as dump_proc,
            subprocess.Popen(
                load_cmd,
                stdin=dump_proc.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                env=load_env,
            ) as load_proc,
        ):
            # Allow dump_proc to receive a SIGPIPE if the load process exits.
            dump_proc.stdout.close()
            dump_err = dump_proc.stderr.read().decode(errors="replace")
            load_err = load_proc.stderr.read().decode(errors="replace")
        if dump_proc.returncode != 0:
            self.log(
                f"Got an error on mysqldump when cloning the test database: {dump_err}"
            )
            sys.exit(dump_proc.returncode)
        if load_proc.returncode != 0:
            self.log(f"Got an error cloning the test database: {load_err}")
            sys.exit(load_proc.returncode)