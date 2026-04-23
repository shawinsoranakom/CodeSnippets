def to_dict(self):
        env = COMMON_ENV_VARIABLES.copy()
        # fmt: off
        # not critical
        env.update({"HF_TOKEN": "".join(["h", "f", "_", "q", "h", "b", "O", "C", "G", "N", "Y", "x", "D", "K", "C", "P", "J", "n", "q", "m", "O", "q", "g", "q", "s", "f", "q", "S", "v", "f", "s", "j", "q", "w", "j", "C", "T"])})
        # fmt: on

        # Do not run tests decorated by @is_flaky on pull requests
        env["RUN_FLAKY"] = os.environ.get("CIRCLE_PULL_REQUEST", "") == ""
        env.update(self.additional_env)

        job = {
            "docker": self.docker_image,
            "environment": env,
        }
        if self.resource_class is not None:
            job["resource_class"] = self.resource_class

        all_options = {**COMMON_PYTEST_OPTIONS, **self.pytest_options}
        pytest_flags = [
            f"--{key}={value}" if (value is not None or key in ["doctest-modules"]) else f"-{key}"
            for key, value in all_options.items()
        ]
        pytest_flags.append(
            f"--make-reports={self.name}" if "examples" in self.name else f"--make-reports=tests_{self.name}"
        )
        # Examples special case: we need to download NLTK files in advance to avoid cuncurrency issues
        timeout_cmd = f"timeout {self.command_timeout} " if self.command_timeout else ""
        marker_cmd = f"-m '{self.marker}'" if self.marker is not None else ""
        junit_flags = " -p no:warning -o junit_family=xunit1 --junitxml=test-results/junit.xml"
        joined_flaky_patterns = "|".join(FLAKY_TEST_FAILURE_PATTERNS)
        repeat_on_failure_flags = f"--reruns 5 --reruns-delay 2 --only-rerun '({joined_flaky_patterns})'"
        parallel = f" << pipeline.parameters.{self.job_name}_parallelism >> "
        steps = [
            "checkout",
            {"attach_workspace": {"at": "test_preparation"}},
            {"run": "apt-get update && apt-get install -y curl"},
            {"run": " && ".join(self.install_steps)},
            {
                "run": {
                    "name": "Download NLTK files",
                    "command": """python -c "import nltk; nltk.download('punkt', quiet=True)" """,
                }
                if "example" in self.name
                else "echo Skipping"
            },
            {
                "run": {
                    "name": "Show installed libraries and their size",
                    "command": """du -h -d 1 "$(pip -V | cut -d ' ' -f 4 | sed 's/pip//g')" | grep -vE "dist-info|_distutils_hack|__pycache__" | sort -h | tee installed.txt || true""",
                }
            },
            {
                "run": {
                    "name": "Show installed libraries and their versions",
                    "command": """pip list --format=freeze | tee installed.txt || true""",
                }
            },
            {
                "run": {
                    "name": "Show biggest libraries",
                    "command": """dpkg-query --show --showformat='${Installed-Size}\t${Package}\n' | sort -rh | head -25 | sort -h | awk '{ package=$2; sub(".*/", "", package); printf("%.5f GB %s\n", $1/1024/1024, package)}' || true""",
                }
            },
            {"run": {"name": "Create `test-results` directory", "command": "mkdir test-results"}},
            {
                "run": {
                    "name": "Get files to test",
                    "command": f'curl -L -o {self.job_name}_test_list.txt <<pipeline.parameters.{self.job_name}_test_list>> --header "Circle-Token: $CIRCLE_TOKEN"'
                    if self.name != "pr_documentation_tests"
                    else 'echo "Skipped"',
                }
            },
            {
                "run": {
                    "name": "Split tests across parallel nodes: show current parallel tests",
                    "command": f"TESTS=$(circleci tests split  --split-by=timings {self.job_name}_test_list.txt) && echo $TESTS > splitted_tests.txt && echo $TESTS | tr ' ' '\n'"
                    if self.parallelism
                    else f"awk '{{printf \"%s \", $0}}' {self.job_name}_test_list.txt > splitted_tests.txt",
                }
            },
            # During the CircleCI docker images build time, we might already (or not) download the data.
            # If it's done already, the files are inside the directory `/test_data/`.
            {
                "run": {
                    "name": "fetch hub objects before pytest",
                    "command": "cp -r /test_data/* . 2>/dev/null || true; python3 utils/fetch_hub_objects_for_ci.py",
                }
            },
            {
                "run": {
                    "name": "download and unzip hub cache",
                    "command": 'curl -L -o huggingface-cache.tar.gz https://huggingface.co/datasets/hf-internal-testing/hf_hub_cache/resolve/main/huggingface-cache.tar.gz && apt-get install pigz && tar --use-compress-program="pigz -d -p 8" -xf huggingface-cache.tar.gz && mv -n hub/* /root/.cache/huggingface/hub/ && ls -la /root/.cache/huggingface/hub/',
                }
            },
            {
                "run": {
                    "name": "Run tests",
                    "command": f"({timeout_cmd} python3 -m pytest {marker_cmd} -n {self.pytest_num_workers} {junit_flags} {repeat_on_failure_flags} {' '.join(pytest_flags)} $(cat splitted_tests.txt) | tee tests_output.txt)",
                }
            },
            {
                "run": {
                    "name": "Check for test crashes",
                    "when": "always",
                    "command": """if [ ! -f tests_output.txt ]; then
                            echo "ERROR: tests_output.txt does not exist - tests may not have run properly"
                            exit 1
                        elif grep -q "crashed and worker restarting disabled" tests_output.txt; then
                            echo "ERROR: Worker crash detected in test output"
                            echo "Found: crashed and worker restarting disabled"
                            exit 1
                        else
                            echo "Tests output file exists and no worker crashes detected"
                        fi""",
                },
            },
            {
                "run": {
                    "name": "Expand to show skipped tests",
                    "when": "always",
                    "command": "python3 .circleci/parse_test_outputs.py --file tests_output.txt --skip",
                }
            },
            {
                "run": {
                    "name": "Failed tests: show reasons",
                    "when": "always",
                    "command": "python3 .circleci/parse_test_outputs.py --file tests_output.txt --fail",
                }
            },
            {
                "run": {
                    "name": "Errors",
                    "when": "always",
                    "command": "python3 .circleci/parse_test_outputs.py --file tests_output.txt --errors",
                }
            },
            {"store_test_results": {"path": "test-results"}},
            {"store_artifacts": {"path": "test-results/junit.xml"}},
            {"store_artifacts": {"path": "reports"}},
            {"store_artifacts": {"path": "tests.txt"}},
            {"store_artifacts": {"path": "splitted_tests.txt"}},
            {"store_artifacts": {"path": "installed.txt"}},
            {"store_artifacts": {"path": "network_debug_report.json"}},
        ]
        if self.parallelism:
            job["parallelism"] = parallel
        job["steps"] = steps
        return job