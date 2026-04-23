def update_sources(xnnpack_path, cmakefile = "XNNPACK/CMakeLists.txt"):
    print(f"Updating sources from {cmakefile}")
    sources = collections.defaultdict(list)
    with open(os.path.join(xnnpack_path, cmakefile)) as cmake:
        lines = cmake.readlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            if lines[i].startswith("INCLUDE"):
                file, _ = handle_singleline_parse(line)
                if file.startswith("cmake/gen/"):
                    path = Path(xnnpack_path) / "XNNPACK" / file
                    local_sources = update_sources(xnnpack_path, path.absolute().as_posix())
                    for k,v in local_sources.items():
                        if k in sources:
                            sources[k] = sources[k] + local_sources[k]
                        else:
                            sources[k] = local_sources[k]

            if lines[i].startswith("SET") and "src/" in lines[i]:
                name, val = handle_singleline_parse(line)
                sources[name].extend(val)
                i+=1
                continue

            if line.startswith("SET") and line.split('(')[1].strip(' \t\n\r') in set(WRAPPER_SRC_NAMES.keys()) | set(SRC_NAMES):
                name = line.split('(')[1].strip(' \t\n\r')
                i += 1
                while i < len(lines) and len(lines[i]) > 0 and ')' not in lines[i]:
                    # remove "src/" at the beginning, remove whitespaces and newline
                    value = lines[i].strip(' \t\n\r')
                    if value not in IGNORED_SOURCES:
                        sources[name].append(value[4:])
                    i += 1
                if i < len(lines) and len(lines[i]) > 4:
                    # remove "src/" at the beginning, possibly ')' at the end
                    value = lines[i].strip(' \t\n\r)')
                    if value not in IGNORED_SOURCES:
                        sources[name].append(value[4:])
            else:
                i += 1
    return sources