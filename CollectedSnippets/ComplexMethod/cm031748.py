def load_raw_data(input: Path) -> RawData:
    if input.is_file():
        with open(input, "r") as fd:
            data = json.load(fd)

        data["_stats_defines"] = {int(k): v for k, v in data["_stats_defines"].items()}
        data["_defines"] = {int(k): v for k, v in data["_defines"].items()}

        return data

    elif input.is_dir():
        stats = collections.Counter[str]()

        for filename in input.iterdir():
            with open(filename) as fd:
                for line in fd:
                    try:
                        key, value = line.split(":")
                    except ValueError:
                        print(
                            f"Unparsable line: '{line.strip()}' in {filename}",
                            file=sys.stderr,
                        )
                        continue
                    # Hack to handle older data files where some uops
                    # are missing an underscore prefix in their name
                    if key.startswith("uops[") and key[5:6] != "_":
                        key = "uops[_" + key[5:]
                    stats[key.strip()] += int(value)
            stats["__nfiles__"] += 1

        data = dict(stats)
        data.update(_load_metadata_from_source())
        return data

    else:
        raise ValueError(f"{input} is not a file or directory path")