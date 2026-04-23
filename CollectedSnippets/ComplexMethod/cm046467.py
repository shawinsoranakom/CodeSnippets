def activate_install_tree(staging_dir: Path, install_dir: Path, host: HostInfo) -> None:
    rollback_dir: Path | None = None
    failed_dir: Path | None = None
    try:
        if install_dir.exists():
            rollback_dir = unique_install_side_path(install_dir, "rollback")
            log(f"moving existing install to rollback path {rollback_dir}")
            os.replace(install_dir, rollback_dir)
            log(f"moved existing install to rollback path {rollback_dir.name}")

        log(f"activating staged install {staging_dir} -> {install_dir}")
        os.replace(staging_dir, install_dir)
        log(f"activated staged install at {install_dir}")
        log(f"confirming activated install tree at {install_dir}")
        confirm_install_tree(install_dir, host)
        log(f"activated install tree confirmed at {install_dir}")
    except Exception as exc:
        log(f"activation failed for staged install: {exc}")
        try:
            if install_dir.exists():
                failed_dir = unique_install_side_path(install_dir, "failed")
                log(f"moving failed active install to {failed_dir}")
                os.replace(install_dir, failed_dir)
            elif staging_dir.exists():
                failed_dir = staging_dir
                staging_dir = None
                log(f"retaining failed staging tree at {failed_dir}")

            if rollback_dir and rollback_dir.exists():
                log(f"restoring rollback path {rollback_dir} -> {install_dir}")
                os.replace(rollback_dir, install_dir)
                log(f"restored previous install from rollback path {rollback_dir.name}")
                if is_busy_lock_error(exc):
                    raise BusyInstallConflict(
                        "staged prebuilt validation passed but the existing install could not be replaced "
                        "because llama.cpp appears to still be in use; restored previous install "
                        f"({textwrap.shorten(str(exc), width = 200, placeholder = '...')})"
                    ) from exc
                raise PrebuiltFallback(
                    "staged prebuilt validation passed but activation failed; restored previous install "
                    f"({textwrap.shorten(str(exc), width = 200, placeholder = '...')})"
                ) from exc
        except (BusyInstallConflict, PrebuiltFallback):
            raise
        except Exception as rollback_exc:
            log(f"rollback after failed activation also failed: {rollback_exc}")

        log(
            "rollback restoration failed; cleaning staging, install, and rollback paths before source build fallback"
        )
        cleanup_error: Exception | None = None
        try:
            cleanup_install_side_paths(
                install_dir,
                staging_dir = staging_dir,
                rollback_dir = rollback_dir,
                failed_dir = failed_dir,
                active_dir = install_dir,
            )
        except Exception as cleanup_exc:
            cleanup_error = cleanup_exc
            log(f"cleanup after rollback failure also failed: {cleanup_exc}")
        details = textwrap.shorten(str(exc), width = 200, placeholder = "...")
        if cleanup_error is not None:
            raise PrebuiltFallback(
                "staged prebuilt validation passed but activation and rollback failed; "
                f"cleanup also reported errors ({details}; cleanup={cleanup_error})"
            ) from exc
        raise PrebuiltFallback(
            "staged prebuilt validation passed but activation and rollback failed; "
            f"cleaned install state for fresh source build ({details})"
        ) from exc
    else:
        if rollback_dir:
            try:
                remove_tree_logged(rollback_dir, "rollback path")
            except Exception as cleanup_exc:
                log(
                    f"non-fatal: rollback cleanup failed after successful activation: {cleanup_exc}"
                )
    finally:
        remove_tree(failed_dir)
        remove_tree(staging_dir)
        prune_install_staging_root(install_dir)