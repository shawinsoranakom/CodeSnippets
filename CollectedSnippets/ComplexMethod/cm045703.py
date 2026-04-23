def _run(self, action, state=None):
        assert self.executable, "`executable` attribute should be set"

        if isinstance(self.executable, (str, os.PathLike)):
            command = shlex.split(os.fspath(self.executable)) + [action]
        else:
            command = [os.fspath(self.executable), action]

        def add_argument(name, value):
            with open(f"{self.temp_dir}/{name}.json", "w", encoding="utf-8") as file:
                json.dump(value, file)
            return [f"--{name}", f"{self.temp_dir_for_executable}/{name}.json"]

        needs_config = action != "spec"
        if needs_config:
            assert self.config, "config attribute is not defined"
            command.extend(add_argument("config", self.config))

        needs_configured_catalog = action == "read"
        if needs_configured_catalog:
            command.extend(add_argument("catalog", self.configured_catalog))

        if state:
            command.extend(add_argument("state", state))

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            env=self.env_vars,
        )
        if process.stdout is not None:
            for line in iter(process.stdout.readline, b""):
                content = line.decode().strip()
                try:
                    message = json.loads(content)
                except ValueError:
                    print("NOT JSON:", content)
                    continue
                if message.get("trace", {}).get("error"):
                    raise AirbyteSourceException(json.dumps(message["trace"]["error"]))
                yield message