def _extract_backup(
    config_dir: Path,
    restore_content: RestoreBackupFileContent,
) -> None:
    """Extract the backup file to the config directory."""
    with (
        TemporaryDirectory() as tempdir,
        securetar.SecureTarArchive(
            restore_content.backup_file_path,
            mode="r",
        ) as ostf,
    ):
        ostf.tar.extractall(
            path=Path(tempdir, "extracted"),
            members=securetar.secure_path(ostf.tar),
            filter="fully_trusted",
        )
        backup_meta_file = Path(tempdir, "extracted", "backup.json")
        backup_meta = json.loads(backup_meta_file.read_text(encoding="utf8"))

        if (
            backup_meta_version := AwesomeVersion(
                backup_meta["homeassistant"]["version"]
            )
        ) > HA_VERSION:
            raise ValueError(
                f"You need at least Home Assistant version {backup_meta_version} to restore this backup"
            )

        with securetar.SecureTarFile(
            Path(
                tempdir,
                "extracted",
                f"homeassistant.tar{'.gz' if backup_meta['compressed'] else ''}",
            ),
            gzip=backup_meta["compressed"],
            password=restore_content.password,
        ) as istf:
            istf.extractall(
                path=Path(tempdir, "homeassistant"),
                members=securetar.secure_path(istf),
                filter="fully_trusted",
            )
            if restore_content.restore_homeassistant:
                keep = list(KEEP_BACKUPS)
                if not restore_content.restore_database:
                    keep.extend(KEEP_DATABASE)
                _clear_configuration_directory(config_dir, keep)
                shutil.copytree(
                    Path(tempdir, "homeassistant", "data"),
                    config_dir,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*(keep)),
                    ignore_dangling_symlinks=True,
                )
            elif restore_content.restore_database:
                for entry in KEEP_DATABASE:
                    entrypath = config_dir / entry

                    if entrypath.is_file():
                        entrypath.unlink()
                    elif entrypath.is_dir():
                        shutil.rmtree(entrypath)

                for entry in KEEP_DATABASE:
                    shutil.copy(
                        Path(tempdir, "homeassistant", "data", entry),
                        config_dir,
                    )