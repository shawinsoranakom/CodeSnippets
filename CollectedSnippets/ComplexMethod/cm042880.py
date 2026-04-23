def check_missing_dependencies():
    """Main function to check for missing dependencies"""
    print("🔍 Analyzing crawl4ai library and docs folders...\n")

    # Get all imports with their file locations
    root_dir = Path('.')
    import_to_files = get_codebase_imports_with_files(root_dir)

    # Get declared dependencies
    declared_deps = get_declared_dependencies()

    # Normalize declared dependencies
    normalized_declared = {normalize_package_name(dep) for dep in declared_deps}

    # Categorize imports
    external_imports = {}
    local_imports = {}

    # Known local packages
    local_packages = {'crawl4ai'}

    for imp, file_info in import_to_files.items():
        # Skip standard library
        if imp in STDLIB_MODULES:
            continue

        # Check if it's a local import
        if any(imp.startswith(local) for local in local_packages):
            local_imports[imp] = file_info
        else:
            external_imports[imp] = file_info

    # Check which external imports are not declared
    not_declared = {}
    declared_imports = {}

    for imp, file_info in external_imports.items():
        normalized_imp = normalize_package_name(imp)

        # Check if import is covered by declared dependencies
        found = False
        for declared in normalized_declared:
            if normalized_imp == declared or normalized_imp.startswith(declared + '.') or declared.startswith(normalized_imp):
                found = True
                break

        if found:
            declared_imports[imp] = file_info
        else:
            not_declared[imp] = file_info

    # Print results
    print(f"📊 Summary:")
    print(f"  - Total unique imports: {len(import_to_files)}")
    print(f"  - External imports: {len(external_imports)}")
    print(f"  - Declared dependencies: {len(declared_deps)}")
    print(f"  - External imports NOT in dependencies: {len(not_declared)}\n")

    if not_declared:
        print("❌ External imports NOT declared in pyproject.toml or requirements.txt:\n")

        # Sort by import name
        for imp in sorted(not_declared.keys()):
            file_info = not_declared[imp]
            print(f"  📦 {imp}")
            if imp in PACKAGE_MAPPINGS:
                print(f"     → Package name: {PACKAGE_MAPPINGS[imp]}")

            # Show up to 3 files that use this import
            for i, (file_path, line_numbers) in enumerate(file_info[:3]):
                # Format line numbers for clickable output
                if len(line_numbers) == 1:
                    print(f"     - {file_path}:{line_numbers[0]}")
                else:
                    # Show first few line numbers
                    line_str = ','.join(str(ln) for ln in line_numbers[:3])
                    if len(line_numbers) > 3:
                        line_str += f"... ({len(line_numbers)} imports)"
                    print(f"     - {file_path}: lines {line_str}")

            if len(file_info) > 3:
                print(f"     ... and {len(file_info) - 3} more files")
            print()

    # Check for potentially unused dependencies
    print("\n🔎 Checking declared dependencies usage...\n")

    # Get all used external packages
    used_packages = set()
    for imp in external_imports.keys():
        normalized = normalize_package_name(imp)
        used_packages.add(normalized)

    # Find unused
    unused = []
    for dep in declared_deps:
        normalized_dep = normalize_package_name(dep)

        # Check if any import uses this dependency
        found_usage = False
        for used in used_packages:
            if used == normalized_dep or used.startswith(normalized_dep) or normalized_dep.startswith(used):
                found_usage = True
                break

        if not found_usage:
            # Some packages are commonly unused directly
            indirect_deps = {'wheel', 'setuptools', 'pip', 'colorama', 'certifi', 'packaging', 'urllib3'}
            if normalized_dep not in indirect_deps:
                unused.append(dep)

    if unused:
        print("⚠️  Declared dependencies with NO imports found:")
        for dep in sorted(unused):
            print(f"  - {dep}")
        print("\n  Note: These might be used indirectly or by other dependencies")
    else:
        print("✅ All declared dependencies have corresponding imports")

    print("\n" + "="*60)
    print("💡 How to use this report:")
    print("  1. Check each ❌ import to see if it's legitimate")
    print("  2. If legitimate, add the package to pyproject.toml")
    print("  3. If it's an internal module or typo, fix the import")
    print("  4. Review unused dependencies - remove if truly not needed")
    print("="*60)