def summary(self, *, verbose: bool = False) -> None:
        longest = max([len(e.name) for e in self.modules], default=0)

        def print_three_column(modinfos: list[ModuleInfo]) -> None:
            names = [modinfo.name for modinfo in modinfos]
            names.sort(key=str.lower)
            # guarantee zip() doesn't drop anything
            while len(names) % 3:
                names.append("")
            for l, m, r in zip(names[::3], names[1::3], names[2::3]):  # noqa: E741
                print("%-*s   %-*s   %-*s" % (longest, l, longest, m, longest, r))

        if verbose and self.builtin_ok:
            print("The following *built-in* modules have been successfully built:")
            print_three_column(self.builtin_ok)
            print()

        if verbose and self.shared_ok:
            print("The following *shared* modules have been successfully built:")
            print_three_column(self.shared_ok)
            print()

        if self.disabled_configure:
            print("The following modules are *disabled* in configure script:")
            print_three_column(self.disabled_configure)
            print()

        if self.disabled_setup:
            print("The following modules are *disabled* in Modules/Setup files:")
            print_three_column(self.disabled_setup)
            print()

        if verbose and self.notavailable:
            print(
                f"The following modules are not available on platform '{self.platform}':"
            )
            print_three_column(self.notavailable)
            print()

        if self.missing:
            print("The necessary bits to build these optional modules were not found:")
            print_three_column(self.missing)
            print("To find the necessary bits, look in configure.ac and config.log.")
            print()

        if self.failed_on_import:
            print(
                "Following modules built successfully "
                "but were removed because they could not be imported:"
            )
            print_three_column(self.failed_on_import)
            print()

        if any(
            modinfo.name == "_ssl" for modinfo in self.missing + self.failed_on_import
        ):
            print("Could not build the ssl module!")
            print("Python requires a OpenSSL 1.1.1 or newer")
            if sysconfig.get_config_var("OPENSSL_LDFLAGS"):
                print("Custom linker flags may require --with-openssl-rpath=auto")
            print()

        disabled = len(self.disabled_configure) + len(self.disabled_setup)
        print(
            f"Checked {len(self.modules)} modules ("
            f"{len(self.builtin_ok)} built-in, "
            f"{len(self.shared_ok)} shared, "
            f"{len(self.notavailable)} n/a on {self.platform}, "
            f"{disabled} disabled, "
            f"{len(self.missing)} missing, "
            f"{len(self.failed_on_import)} failed on import)"
        )