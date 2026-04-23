def smoke_test_modules(package: str):
    cwd = os.getcwd()
    for module in get_modules_for_package(package):
        if module["repo"]:
            if not os.path.exists(f"{cwd}/{module['repo_name']}"):
                print(f"Path does not exist: {cwd}/{module['repo_name']}")
                try:
                    subprocess.check_output(
                        f"git clone --depth 1 {module['repo']}",
                        stderr=subprocess.STDOUT,
                        shell=True,
                    )
                except subprocess.CalledProcessError as exc:
                    raise RuntimeError(
                        f"Cloning {module['repo']} FAIL: {exc.returncode} Output: {exc.output}"
                    ) from exc
            try:
                smoke_test_command = f"python3 {module['smoke_test']}"
                if target_os == "windows":
                    smoke_test_command = f"python {module['smoke_test']}"
                output = subprocess.check_output(
                    smoke_test_command,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    universal_newlines=True,
                )
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    f"Module {module['name']} FAIL: {exc.returncode} Output: {exc.output}"
                ) from exc
            else:
                print(f"Output: \n{output}\n")