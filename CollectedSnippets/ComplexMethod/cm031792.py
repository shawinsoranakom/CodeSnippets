def parse_setup_file(self, setup_file: pathlib.Path) -> Iterable[ModuleInfo]:
        """Parse a Modules/Setup file"""
        assign_var = re.compile(r"^\w+=")  # EGG_SPAM=foo
        # default to static module
        state = ModuleState.BUILTIN
        logger.debug("Parsing Setup file %s", setup_file)
        with open(setup_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or assign_var.match(line):
                    continue
                match line.split():
                    case ["*shared*"]:
                        state = ModuleState.SHARED
                    case ["*static*"]:
                        state = ModuleState.BUILTIN
                    case ["*disabled*"]:
                        state = ModuleState.DISABLED
                    case ["*noconfig*"]:
                        continue
                    case [*items]:
                        if state == ModuleState.DISABLED:
                            # *disabled* can disable multiple modules per line
                            for item in items:
                                modinfo = ModuleInfo(item, state)
                                logger.debug("Found %s in %s", modinfo, setup_file)
                                yield modinfo
                        elif state in {ModuleState.SHARED, ModuleState.BUILTIN}:
                            # *shared* and *static*, first item is the name of the module.
                            modinfo = ModuleInfo(items[0], state)
                            logger.debug("Found %s in %s", modinfo, setup_file)
                            yield modinfo