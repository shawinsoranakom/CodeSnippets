def build_fbcode_re(
        self,
    ) -> None:
        with dynamo_timed("compile_file"):
            command = shlex.split(self.get_command_line())
            try:
                output_path = self._target_file
                # When we build remotely, we need to make sure to carefully copy any files
                # that are required during the compilation process into our build directly.
                # This is where all of the ATen/c10/Torch includes come from.
                torch_includes_path = os.path.join(_TORCH_PATH, "include")
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Copy everything to tmp compilation folder
                    shutil.copy(_LINKER_SCRIPT, os.path.join(tmp_dir, "script.ld"))
                    for src in self._orig_source_paths:
                        shutil.copy(src, os.path.join(tmp_dir, os.path.basename(src)))
                    dest_include_path = os.path.join(tmp_dir, "include")
                    shutil.copytree(torch_includes_path, dest_include_path)

                    # Copy precompiled header (.h and .gch/.pch) into the
                    # build directory and rewrite the -include flag so the
                    # compiler can find it.
                    pch_header = self._build_option.precompiled_header
                    if pch_header and os.path.isfile(pch_header):
                        pch_ext = ".pch" if _IS_WINDOWS or not is_gcc() else ".gch"
                        pch_compiled = pch_header + pch_ext
                        pch_basename = os.path.basename(pch_header)
                        shutil.copy(pch_header, os.path.join(tmp_dir, pch_basename))
                        if os.path.isfile(pch_compiled):
                            shutil.copy(
                                pch_compiled,
                                os.path.join(tmp_dir, pch_basename + pch_ext),
                            )
                        command = [
                            pch_basename if arg == pch_header else arg
                            for arg in command
                        ]

                    # Relocatable PCH stores include paths relative to
                    # -isysroot.  Set sysroot to the tmp build dir so
                    # paths resolve correctly in both precompilation and
                    # later kernel compilations that consume the PCH.
                    if self._precompiling or (
                        pch_header and os.path.isfile(pch_header)
                    ):
                        command[1:1] = ["-isysroot", "."]

                    # Run the build, raising RuntimeError on failure instead of
                    # SkipFrame so compilation errors propagate rather than
                    # silently falling back to eager execution.
                    tmp_output_path = _run_build_command(
                        command,
                        tmp_dir,
                        os.path.basename(output_path),
                        exception_class=RuntimeError,
                    )
                    # Copy output from the build
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    shutil.copy(tmp_output_path, output_path)
                    if output_path.endswith(".o"):
                        os.chmod(output_path, 0o644)
                    elif output_path.endswith(".so"):
                        os.chmod(output_path, 0o755)
            except subprocess.CalledProcessError as e:
                raise exc.CppCompileError(command, e.output.decode("utf-8")) from e