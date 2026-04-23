def __init__(
        self,
        args: EnvironmentConfig,
        resource: Resource,
        load: bool = True,
    ) -> None:
        self.args = args
        self.resource = resource
        self.platform, self.version, self.arch, self.provider = self.resource.as_tuple()
        self.stage = args.remote_stage
        self.client = HttpClient(args)
        self.connection = None
        self.instance_id = None
        self.endpoint = None
        self.default_endpoint = args.remote_endpoint or self.DEFAULT_ENDPOINT
        self.retries = 3
        self.ci_provider = get_ci_provider()
        self.label = self.resource.get_label()

        stripped_label = re.sub('[^A-Za-z0-9_.]+', '-', self.label).strip('-')

        self.name = f"{stripped_label}-{self.stage}"  # turn the label into something suitable for use as a filename

        self.path = os.path.expanduser(f'~/.ansible/test/instances/{self.name}')
        self.ssh_key = SshKey(args)

        if self.resource.persist and load and self._load():
            try:
                display.info(f'Checking existing {self.label} instance using: {self._uri}', verbosity=1)

                self.connection = self.get(always_raise_on=[404])

                display.info(f'Loaded existing {self.label} instance.', verbosity=1)
            except HttpError as ex:
                if ex.status != 404:
                    raise

                self._clear()

                display.info(f'Cleared stale {self.label} instance.', verbosity=1)

                self.instance_id = None
                self.endpoint = None
        elif not self.resource.persist:
            self.instance_id = None
            self.endpoint = None
            self._clear()

        if self.instance_id:
            self.started: bool = True
        else:
            self.started = False
            self.instance_id = str(uuid.uuid4())
            self.endpoint = None

            display.sensitive.add(self.instance_id)

        if not self.endpoint:
            self.endpoint = self.default_endpoint