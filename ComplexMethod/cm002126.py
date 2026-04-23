def __post_init__(self):
        # Deal with defaults for mutable attributes.
        if self.additional_env is None:
            self.additional_env = {}
        if self.docker_image is None:
            # Let's avoid changing the default list and make a copy.
            self.docker_image = copy.deepcopy(DEFAULT_DOCKER_IMAGE)
        else:
            # BIG HACK WILL REMOVE ONCE FETCHER IS UPDATED
            print(os.environ.get("GIT_COMMIT_MESSAGE"))
            if (
                "[build-ci-image]" in os.environ.get("GIT_COMMIT_MESSAGE", "")
                or os.environ.get("GIT_COMMIT_MESSAGE", "") == "dev-ci"
            ):
                self.docker_image[0]["image"] = f"{self.docker_image[0]['image']}:dev"
            print(f"Using {self.docker_image} docker image")
        if self.install_steps is None:
            self.install_steps = ["uv pip install ."]
        # Use a custom patched pytest to force exit the process at the end, to avoid `Too long with no output (exceeded 10m0s): context deadline exceeded`
        self.install_steps.append("uv pip install git+https://github.com/ydshieh/pytest.git@8.4.1-ydshieh")
        # Install pytest-random-order plugin for test randomization
        self.install_steps.append("uv pip install pytest-random-order")
        if self.pytest_options is None:
            self.pytest_options = {}
        if isinstance(self.tests_to_run, str):
            self.tests_to_run = [self.tests_to_run]
        else:
            test_file = os.path.join("test_preparation", f"{self.job_name}_test_list.txt")
            print("Looking for ", test_file)
            if os.path.exists(test_file):
                with open(test_file, encoding="utf-8") as f:
                    expanded_tests = f.read().strip().split("\n")
                self.tests_to_run = expanded_tests
                print("Found:", expanded_tests)
            else:
                self.tests_to_run = []
                print("not Found")