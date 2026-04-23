def check_metadata(prof, op_name, metadata_key):
            with TemporaryFileName(mode="w+") as fname:
                prof.export_chrome_trace(fname)
                with open(fname) as f:
                    events = json.load(f)["traceEvents"]
                    found_op = False
                    for e in events:
                        if "name" in e and "args" in e and e["name"] == op_name:
                            if metadata_key not in e["args"]:
                                raise AssertionError(
                                    f"Metadata for '{op_name}' in Chrome trace did not contain '{metadata_key}'."
                                )
                            found_op = True
                    if not found_op:
                        raise AssertionError(
                            f"Could not find op '{op_name}' in Chrome trace."
                        )
                found_op = False
                for event in prof.events():
                    if event.name == op_name:
                        if metadata_key not in event.metadata_json:
                            raise AssertionError(
                                f"Metadata for '{op_name}' in FunctionEvent did not contain '{metadata_key}'."
                            )
                        found_op = True
                if not found_op:
                    raise AssertionError(
                        f"Could not find op '{op_name}' in prof.events()."
                    )