def wrapper(*args, **kwargs):
        if os.getenv("_INSIDE_SUB_PROCESS", None) == "1":
            func(*args, **kwargs)
        else:
            test = " ".join(os.environ.get("PYTEST_CURRENT_TEST").split(" ")[:-1])
            try:
                env = copy.deepcopy(os.environ)
                env["_INSIDE_SUB_PROCESS"] = "1"
                # This prevents the entries in `short test summary info` given by the subprocess being truncated. so the
                # full information can be passed to the parent pytest process.
                # See: https://docs.pytest.org/en/stable/explanation/ci.html
                env["CI"] = "true"

                # If not subclass of `unitTest.TestCase` and `pytestconfig` is used: try to grab and use the arguments
                if "pytestconfig" in kwargs:
                    command = list(kwargs["pytestconfig"].invocation_params.args)
                    for idx, x in enumerate(command):
                        if x in kwargs["pytestconfig"].args:
                            test = test.split("::")[1:]
                            command[idx] = "::".join([f"{func.__globals__['__file__']}"] + test)
                    command = [f"{sys.executable}", "-m", "pytest"] + command
                    command = [x for x in command if x != "--no-summary"]
                # Otherwise, simply run the test with no option at all
                else:
                    command = [f"{sys.executable}", "-m", "pytest", f"{test}"]

                subprocess.run(command, env=env, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                exception_message = e.stdout.decode()
                lines = exception_message.split("\n")
                # Add a first line with more informative information instead of just `= test session starts =`.
                # This makes the `short test summary info` section more useful.
                if "= test session starts =" in lines[0]:
                    text = ""
                    for line in lines[1:]:
                        if line.startswith("FAILED "):
                            text = line[len("FAILED ") :]
                            text = "".join(text.split(" - ")[1:])
                        elif line.startswith("=") and line.endswith("=") and " failed in " in line:
                            break
                        elif len(text) > 0:
                            text += f"\n{line}"
                    text = "(subprocess) " + text
                    lines = [text] + lines
                exception_message = "\n".join(lines)
                raise pytest.fail(exception_message, pytrace=False)