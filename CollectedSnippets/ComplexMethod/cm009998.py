def check_headeronly_symbols(install_root: Path) -> None:
    """
    Test that header-only utility headers still expose symbols with TORCH_STABLE_ONLY.
    """
    include_dir = install_root / "include"
    if not include_dir.exists():
        raise AssertionError(f"Expected {include_dir} to be present")

    # Find all headers in torch/headeronly
    headeronly_dir = include_dir / "torch" / "headeronly"
    if not headeronly_dir.exists():
        raise AssertionError(f"Expected {headeronly_dir} to be present")
    headeronly_headers = list(headeronly_dir.rglob("*.h"))
    if not headeronly_headers:
        raise RuntimeError("Could not find any headeronly headers")

    # Filter out platform-specific headers that may not compile everywhere
    platform_specific_keywords = [
        "cpu/vec",
    ]

    filtered_headers = []
    for header in headeronly_headers:
        rel_path = header.relative_to(include_dir).as_posix()
        if not any(
            keyword in rel_path.lower() for keyword in platform_specific_keywords
        ):
            filtered_headers.append(header)

    includes = []
    for header in filtered_headers:
        rel_path = header.relative_to(include_dir)
        includes.append(f"#include <{rel_path.as_posix()}>")

    includes_str = "\n".join(includes)
    test_headeronly_content = f"""
{includes_str}
int main() {{ return 0; }}
"""

    compile_flags = [
        "g++",
        "-std=c++17",
        f"-I{include_dir}",
        f"-I{include_dir}/torch/csrc/api/include",
        "-c",
        "-DTORCH_STABLE_ONLY",
    ]

    symbols_headeronly = _compile_and_extract_symbols(
        cpp_content=test_headeronly_content,
        compile_flags=compile_flags,
    )
    num_symbols_headeronly = len(symbols_headeronly)
    print(f"Found {num_symbols_headeronly} symbols in torch/headeronly")
    if num_symbols_headeronly <= 0:
        raise AssertionError(
            f"Expected headeronly headers to expose symbols with TORCH_STABLE_ONLY, "
            f"but found {num_symbols_headeronly} symbols"
        )