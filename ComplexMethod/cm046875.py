def try_execute(commands, force_complete = False):
    for command in commands:
        with subprocess.Popen(
            command,
            shell = True,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            bufsize = 1,
        ) as sp:
            for line in sp.stdout:
                line = line.decode("utf-8", errors = "replace")
                if "undefined reference" in line:
                    raise RuntimeError(
                        f"*** Unsloth: Failed compiling llama.cpp with {line}. Please report this ASAP!"
                    )
                elif "deprecated" in line:
                    return "CMAKE"
                elif "Unknown argument" in line:
                    raise RuntimeError(
                        f"*** Unsloth: Failed compiling llama.cpp with {line}. Please report this ASAP!"
                    )
                elif "***" in line:
                    raise RuntimeError(
                        f"*** Unsloth: Failed compiling llama.cpp with {line}. Please report this ASAP!"
                    )
                print(line, flush = True, end = "")
            if force_complete and sp.returncode is not None and sp.returncode != 0:
                raise subprocess.CalledProcessError(sp.returncode, sp.args)
    return None