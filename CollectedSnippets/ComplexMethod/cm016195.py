def create(
        self,
        *,
        remove_if_exists: bool = False,
        assume_yes: bool = False,
    ) -> Path:
        """Create a virtual environment."""
        if self.prefix.exists():
            if remove_if_exists:
                # If the venv directory already exists, remove it first
                if not self.is_venv():
                    raise RuntimeError(
                        f"The path {self.prefix} already exists and is not a virtual environment. "
                        "Please remove it manually or choose a different prefix."
                    )
                if any(
                    Path(p).absolute().samefile(self.prefix)
                    for p in [
                        sys.prefix,
                        sys.exec_prefix,
                        sys.base_prefix,
                        sys.base_exec_prefix,
                    ]
                ):
                    raise RuntimeError(
                        f"The path {self.prefix} trying to remove is the same as the interpreter "
                        "to run this script. Please choose a different prefix or deactivate the "
                        "current virtual environment."
                    )
                if any(
                    Path(
                        self.base_python(
                            "-c",
                            f"import os, sys; print(os.path.abspath({p}))",
                            capture_output=True,
                        ).stdout.strip()
                    )
                    .absolute()
                    .samefile(self.prefix)
                    for p in [
                        "sys.prefix",
                        "sys.exec_prefix",
                        "sys.base_prefix",
                        "sys.base_exec_prefix",
                    ]
                ):
                    raise RuntimeError(
                        f"The Python executable {self.base_executable} trying to remove is the "
                        "same as the interpreter to create the virtual environment. Please choose "
                        "a different prefix or a different Python interpreter."
                    )
                if not assume_yes:
                    answer = input(
                        f"The virtual environment {self.prefix} already exists. "
                        "Do you want to remove it and recreate it? [y/N] "
                    )
                    if answer.lower() not in ("y", "yes"):
                        if answer.lower() not in ("n", "no", ""):
                            print(f"Invalid answer: {answer!r}")
                        else:
                            print(f"Aborting due to existing prefix: {self.prefix}")
                        sys.exit(1)

                print(f"Removing existing venv: {self.prefix}")
                _remove_existing(self.prefix)
            else:
                raise RuntimeError(f"Path {self.prefix} already exists.")

        print(f"Creating venv (Python {self.base_python_version()}): {self.prefix}")
        self.base_python("-m", "venv", str(self.prefix))
        if not self.is_venv():
            raise AssertionError("Failed to create virtual environment.")
        (self.prefix / ".gitignore").write_text("*\n", encoding="utf-8")

        if LINUX:
            activate_script = self.activate_script
            st_mode = activate_script.stat().st_mode
            # The activate script may be read-only and we need to add write permissions
            activate_script.chmod(st_mode | 0o200)
            with activate_script.open(mode="a", encoding="utf-8") as f:
                f.write(
                    "\n"
                    + textwrap.dedent(
                        f"""
                        # Add NVIDIA PyPI packages to LD_LIBRARY_PATH
                        export LD_LIBRARY_PATH="$(
                            {self.executable.name} - <<EOS
                        import glob
                        import itertools
                        import os
                        import site

                        nvidia_libs = [
                            p.rstrip("/")
                            for p in itertools.chain.from_iterable(
                                glob.iglob(f"{{site_dir}}/{{pattern}}/", recursive=True)
                                for site_dir in site.getsitepackages()
                                for pattern in ("nvidia/**/lib", "cu*/**/lib")
                            )
                        ]
                        ld_library_path = os.getenv("LD_LIBRARY_PATH", "").split(os.pathsep)
                        print(os.pathsep.join(dict.fromkeys(nvidia_libs + ld_library_path)))
                        EOS
                        )"
                        """
                    ).strip()
                    + "\n"
                )
            # Change the file mode back
            activate_script.chmod(st_mode)

        return self.ensure()