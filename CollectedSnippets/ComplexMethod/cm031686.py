def build(
        self,
        *,
        comment: str = "",
        force: bool = False,
        jit_stencils: pathlib.Path,
    ) -> None:
        """Build jit_stencils.h in the given directory."""
        jit_stencils.parent.mkdir(parents=True, exist_ok=True)
        if not self.stable:
            warning = f"JIT support for {self.triple} is still experimental!"
            request = "Please report any issues you encounter.".center(len(warning))
            if self.llvm_version != _llvm._LLVM_VERSION:
                request = f"Warning! Building with an LLVM version other than {_llvm._LLVM_VERSION} is not supported."
            outline = "=" * len(warning)
            print("\n".join(["", outline, warning, request, outline, ""]))
        digest = f"// {self._compute_digest()}\n"
        if (
            not force
            and jit_stencils.exists()
            and jit_stencils.read_text().startswith(digest)
        ):
            return
        stencil_groups = ASYNCIO_RUNNER.run(self._build_stencils())
        jit_stencils_new = jit_stencils.parent / "jit_stencils.h.new"
        try:
            with jit_stencils_new.open("w") as file:
                file.write(digest)
                if comment:
                    file.write(f"// {comment}\n")
                file.write("\n")
                for line in _writer.dump(stencil_groups, self.known_symbols):
                    file.write(f"{line}\n")
            try:
                jit_stencils_new.replace(jit_stencils)
            except FileNotFoundError:
                # another process probably already moved the file
                if not jit_stencils.is_file():
                    raise
        finally:
            jit_stencils_new.unlink(missing_ok=True)