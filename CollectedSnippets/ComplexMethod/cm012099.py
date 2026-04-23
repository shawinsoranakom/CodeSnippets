def _search_for_file(suffix: str, errmsg: str) -> str:
        spec = importlib.machinery.PathFinder.find_spec("halide")
        if spec is None or not spec.submodule_search_locations:
            raise RuntimeError("halide python bindings not installed")
        try:
            search = spec.submodule_search_locations[0]
            for file in os.listdir(search):
                if file.endswith(".so"):
                    try:
                        out = subprocess.check_output(
                            ["ldd", os.path.join(search, file)]
                        )
                    except subprocess.SubprocessError:
                        continue
                    m = re.search(r"(/.*)/libHalide.so", out.decode("utf-8"))
                    if m:
                        path = os.path.join(os.path.abspath(m.group(1)), suffix)
                        if os.path.exists(path):
                            return os.path.abspath(path)
        except Exception as e:
            raise RuntimeError(errmsg) from e
        raise RuntimeError(errmsg)