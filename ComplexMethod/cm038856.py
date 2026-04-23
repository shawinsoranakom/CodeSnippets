def main():
    parser = argparse.ArgumentParser(
        description="Autotune Helion kernels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1] if "Usage:" in __doc__ else "",
    )

    parser.add_argument(
        "--kernels",
        nargs="+",
        help="Kernel(s) to autotune (default: all kernels)",
    )

    parser.add_argument(
        "--config-dir",
        type=str,
        help="Config directory for config files (default: vLLM helion configs dir)",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available Helion kernels and exit",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Force re-autotuning even if configs already exist for the "
            "platform and config keys"
        ),
    )

    parser.add_argument(
        "--autotune-effort",
        type=str,
        default="quick",
        help=(
            "Helion autotune effort level: 'quick' (smaller search) or "
            "'full' (full search budget) (default: quick)"
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    import logging

    if args.verbose:
        logging.getLogger("vllm").setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        logger.debug("Arguments: %s", vars(args))
    else:
        logging.getLogger("vllm").setLevel(logging.INFO)

    if args.list:
        list_kernels()
        return

    if not check_requirements():
        sys.exit(1)

    platform = get_canonical_gpu_name()
    logger.info("Detected GPU platform: %s", platform)

    config_manager = (
        ConfigManager(args.config_dir) if args.config_dir else ConfigManager()
    )

    try:
        config_manager.ensure_base_dir_writable()
    except OSError as e:
        logger.error("Failed to access config directory: %s", e)
        sys.exit(1)

    kernels_to_autotune = get_kernels_to_autotune(args.kernels)

    logger.info(
        "Will autotune %d kernel(s) for platform '%s': %s",
        len(kernels_to_autotune),
        platform,
        kernels_to_autotune,
    )

    results = {}
    for kernel_name in kernels_to_autotune:
        result = autotune_kernel(
            kernel_name, platform, config_manager, args.force, args.autotune_effort
        )
        results[kernel_name] = result

    success = summarize_results(results)
    sys.exit(0 if success else 1)