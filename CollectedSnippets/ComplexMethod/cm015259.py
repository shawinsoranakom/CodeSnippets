def find_spec(self, fullname, path, target):
                """Try to find the original spec for module_a using all the
                remaining meta_path finders."""
                if fullname != "module_a":
                    return None
                spec = None
                for finder in sys.meta_path:
                    if finder is self:
                        continue
                    if hasattr(finder, "find_spec"):
                        spec = finder.find_spec(fullname, path, target=target)
                    elif hasattr(finder, "load_module"):
                        spec = spec_from_loader(fullname, finder)
                    if spec is not None:
                        break
                if spec is None or not isinstance(spec.loader, SourceFileLoader):
                    raise AssertionError(
                        f"Expected SourceFileLoader, got {type(spec.loader) if spec else None}"
                    )
                spec.loader = LoaderThatRemapsModuleA(
                    spec.loader.name, spec.loader.path
                )
                return spec