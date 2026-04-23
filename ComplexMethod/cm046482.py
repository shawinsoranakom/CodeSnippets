def main() -> int:
    args = parse_args()
    if args.resolve_llama_tag is not None:
        resolved = resolve_requested_llama_tag(
            args.resolve_llama_tag,
            args.published_repo,
            args.published_release_tag or "",
        )
        emit_resolver_output(
            {
                "requested_tag": normalized_requested_llama_tag(args.resolve_llama_tag),
                "llama_tag": resolved,
            },
            output_format = args.output_format,
        )
        return EXIT_SUCCESS

    if args.resolve_install_tag is not None:
        resolved = resolve_requested_install_tag(
            args.resolve_install_tag,
            args.published_release_tag or "",
            args.published_repo,
        )
        emit_resolver_output(
            {
                "requested_tag": normalized_requested_llama_tag(
                    args.resolve_install_tag
                ),
                "llama_tag": resolved,
            },
            output_format = args.output_format,
        )
        return EXIT_SUCCESS

    if args.resolve_source_build is not None:
        plan = resolve_source_build_plan(
            args.resolve_source_build,
            args.published_repo,
            args.published_release_tag or "",
        )
        emit_resolver_output(
            {
                "requested_tag": normalized_requested_llama_tag(
                    args.resolve_source_build
                ),
                "source_url": plan.source_url,
                "source_ref_kind": plan.source_ref_kind,
                "source_ref": plan.source_ref,
                "compatibility_upstream_tag": plan.compatibility_upstream_tag,
            },
            output_format = args.output_format,
        )
        return EXIT_SUCCESS

    if not args.install_dir:
        raise SystemExit(
            "install_llama_prebuilt.py: --install-dir is required unless --resolve-llama-tag, --resolve-install-tag, or --resolve-source-build is used"
        )
    install_prebuilt(
        install_dir = Path(args.install_dir).expanduser().resolve(),
        llama_tag = args.llama_tag,
        published_repo = args.published_repo,
        published_release_tag = args.published_release_tag or "",
        simple_policy = args.simple_policy,
    )
    return EXIT_SUCCESS