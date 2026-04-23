def setUpClass(cls):
        # Build versioned extensions
        base_dir = Path(__file__).parent

        try:
            import libtorch_agn_2_9  # noqa: F401
        except Exception:
            install_cpp_extension(
                extension_root=base_dir / "libtorch_agn_2_9_extension"
            )

        # Only build 2.X extension if running on PyTorch 2.X+
        import re

        version_parts = torch.__version__.split(".")
        current_major = int(version_parts[0])
        # Extract just the numeric part of the minor version (handles "10+git", "10a1", etc.)
        current_minor = int(re.match(r"\d+", version_parts[1]).group())

        if (current_major > 2) or (current_major == 2 and current_minor >= 10):
            try:
                import libtorch_agn_2_10  # noqa: F401
            except Exception:
                install_cpp_extension(
                    extension_root=base_dir / "libtorch_agn_2_10_extension"
                )
        else:
            print(f"Skipping 2.10 extension (running on PyTorch {torch.__version__})")

        if (current_major > 2) or (current_major == 2 and current_minor >= 11):
            try:
                import libtorch_agn_2_11  # noqa: F401
            except Exception:
                install_cpp_extension(
                    extension_root=base_dir / "libtorch_agn_2_11_extension"
                )
        else:
            print(f"Skipping 2.11 extension (running on PyTorch {torch.__version__})")

        if (current_major > 2) or (current_major == 2 and current_minor >= 12):
            try:
                import libtorch_agn_2_12  # noqa: F401
            except Exception:
                install_cpp_extension(
                    extension_root=base_dir / "libtorch_agn_2_12_extension"
                )
        else:
            print(f"Skipping 2.12 extension (running on PyTorch {torch.__version__})")