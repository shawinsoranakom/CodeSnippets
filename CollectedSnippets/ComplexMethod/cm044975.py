def atomic_write_json(target_file: Path, payload: dict[str, Any]) -> None:
        """Atomically write JSON while preserving existing mode bits when possible."""
        temp_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=target_file.parent,
                prefix=f"{target_file.name}.",
                suffix=".tmp",
                delete=False,
            ) as f:
                temp_path = Path(f.name)
                json.dump(payload, f, indent=4)
                f.write('\n')

            if target_file.exists():
                try:
                    existing_stat = target_file.stat()
                    os.chmod(temp_path, stat.S_IMODE(existing_stat.st_mode))
                    if hasattr(os, "chown"):
                        try:
                            os.chown(temp_path, existing_stat.st_uid, existing_stat.st_gid)
                        except PermissionError:
                            # Best-effort owner/group preservation without requiring elevated privileges.
                            pass
                except OSError:
                    # Best-effort metadata preservation; data safety is prioritized.
                    pass

            os.replace(temp_path, target_file)
        except Exception:
            if temp_path and temp_path.exists():
                temp_path.unlink()
            raise