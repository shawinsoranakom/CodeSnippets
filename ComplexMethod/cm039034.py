def has_openmp_flags(target):
    """Return whether target sources use OpenMP flags.

    Make sure that both compiler and linker source use OpenMP.
    Look at `get_meson_info` docstring to see what `target` looks like.
    """
    target_sources = target["target_sources"]

    target_use_openmp_flags = any(
        has_source_openmp_flags(target_source) for target_source in target_sources
    )

    if not target_use_openmp_flags:
        return False

    # When the target use OpenMP we expect a compiler + linker source and we
    # want to make sure that both the compiler and the linker use OpenMP
    assert len(target_sources) == 2
    compiler_source, linker_source = target_sources
    assert "compiler" in compiler_source
    assert "linker" in linker_source

    compiler_use_openmp_flags = any(
        "openmp" in arg for arg in compiler_source["parameters"]
    )
    linker_use_openmp_flags = any(
        "openmp" in arg for arg in linker_source["parameters"]
    )

    assert compiler_use_openmp_flags == linker_use_openmp_flags
    return compiler_use_openmp_flags