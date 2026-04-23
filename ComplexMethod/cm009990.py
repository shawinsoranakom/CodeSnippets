def generate_embedded_hsa_header(
    hsa_dir: Path, output_file: Path, subdirs: list[str]
) -> int:
    """
    Generate a C++ header file embedding all .co files from specified subdirectories.

    Args:
        hsa_dir: Base directory containing hsa files (e.g., third_party/aiter/hsa)
        output_file: Path to the output header file
        subdirs: List of subdirectories to scan for .co files (e.g., ["gfx942/fmha_v3_bwd", "gfx950/fmha_v3_bwd"])

    Returns:
        Number of .co files embedded
    """
    # Collect all .co files
    co_files: list[tuple[str, Path]] = []
    for subdir in subdirs:
        pattern_dir = hsa_dir / subdir
        if pattern_dir.exists():
            for co_file in sorted(pattern_dir.glob("*.co")):
                # Key format: hsa/gfx942/fmha_v3_bwd/xxx.co
                # Use as_posix() to ensure forward slashes on all platforms
                rel_path = co_file.relative_to(hsa_dir).as_posix()
                map_key = f"hsa/{rel_path}"
                co_files.append((map_key, co_file))

    if not co_files:
        print(f"Warning: No .co files found in {hsa_dir} under {subdirs}")
        return 0

    # Generate header content
    # Using std::string_view instead of std::span<const unsigned char> for C++17 compatibility
    # std::string_view provides .data() method which is what hipModuleLoadData needs
    lines = [
        "// Auto-generated file. Do not edit.",
        "// Embedded AITER HSA binary files for fmha_v3_bwd",
        "#pragma once",
        "",
        "#include <cstdint>",
        "#include <string>",
        "#include <string_view>",
        "#include <unordered_map>",
        "",
        "// Define AITER_EMBEDDED_HSA_MAP macro so that aiter_hip_common.h",
        "// can detect the embedded map is available via #if defined(AITER_EMBEDDED_HSA_MAP)",
        "#define AITER_EMBEDDED_HSA_MAP ::aiter_hsa::embedded_hsa_map",
        "",
        "namespace aiter_hsa {",
        "",
    ]

    # Generate array declarations and map entries
    array_entries = []
    for map_key, co_file in co_files:
        with open(co_file, "rb") as f:
            data = f.read()

        # Only generate array and map entry if file has content
        if len(data) > 0:
            safe_name = sanitize_identifier(co_file.relative_to(hsa_dir).as_posix())
            array_name = f"data_{safe_name}"
            file_size = len(data)
            array_entries.append((map_key, array_name, file_size))

            hex_array = bytes_to_hex_array(data)
            lines.append(
                f"alignas(4096) inline const unsigned char {array_name}[] = {{\n    {hex_array}\n}};"
            )
            lines.append("")

    # Generate the map
    lines.append(
        "inline const std::unordered_map<std::string, std::string_view> embedded_hsa_map = {"
    )
    for map_key, array_name, file_size in array_entries:
        lines.append(
            f'    {{"{map_key}", std::string_view(reinterpret_cast<const char*>({array_name}), {file_size})}},'
        )
    lines.append("};")
    lines.append("")
    lines.append("} // namespace aiter_hsa")
    lines.append("")

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    return len(array_entries)