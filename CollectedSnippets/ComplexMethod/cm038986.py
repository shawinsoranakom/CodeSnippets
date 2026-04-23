def GetExtension(target, extra_patterns):
    """Return the file extension that best represents a target.

    For targets that generate multiple outputs it is important to return a
    consistent 'canonical' extension. Ultimately the goal is to group build steps
    by type."""
    for output in target.targets:
        if extra_patterns:
            for fn_pattern in extra_patterns.split(";"):
                if fnmatch.fnmatch(output, "*" + fn_pattern + "*"):
                    return fn_pattern
        # Not a true extension, but a good grouping.
        if output.endswith("type_mappings"):
            extension = "type_mappings"
            break

        # Capture two extensions if present. For example: file.javac.jar should
        # be distinguished from file.interface.jar.
        root, ext1 = os.path.splitext(output)
        _, ext2 = os.path.splitext(root)
        extension = ext2 + ext1  # Preserve the order in the file name.

        if len(extension) == 0:
            extension = "(no extension found)"

        if ext1 in [".pdb", ".dll", ".exe"]:
            extension = "PEFile (linking)"
            # Make sure that .dll and .exe are grouped together and that the
            # .dll.lib files don't cause these to be listed as libraries
            break
        if ext1 in [".so", ".TOC"]:
            extension = ".so (linking)"
            # Attempt to identify linking, avoid identifying as '.TOC'
            break
        # Make sure .obj files don't get categorized as mojo files
        if ext1 in [".obj", ".o"]:
            break
        # Jars are the canonical output of java targets.
        if ext1 == ".jar":
            break
        # Normalize all mojo related outputs to 'mojo'.
        if output.count(".mojom") > 0:
            extension = "mojo"
            break
    return extension