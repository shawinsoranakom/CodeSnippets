def download_pack(
        self, pack_id: str, target_dir: Optional[Path] = None
    ) -> Path:
        """Download preset ZIP from catalog.

        Args:
            pack_id: ID of the preset to download
            target_dir: Directory to save ZIP file (defaults to cache directory)

        Returns:
            Path to downloaded ZIP file

        Raises:
            PresetError: If pack not found or download fails
        """
        import urllib.request
        import urllib.error

        pack_info = self.get_pack_info(pack_id)
        if not pack_info:
            raise PresetError(
                f"Preset '{pack_id}' not found in catalog"
            )

        # Bundled presets without a download URL must be installed locally
        if pack_info.get("bundled") and not pack_info.get("download_url"):
            from .extensions import REINSTALL_COMMAND
            raise PresetError(
                f"Preset '{pack_id}' is bundled with spec-kit and has no download URL. "
                f"It should be installed from the local package. "
                f"Use 'specify preset add {pack_id}' to install from the bundled package, "
                f"or reinstall spec-kit if the bundled files are missing: {REINSTALL_COMMAND}"
            )

        if not pack_info.get("_install_allowed", True):
            catalog_name = pack_info.get("_catalog_name", "unknown")
            raise PresetError(
                f"Preset '{pack_id}' is from the '{catalog_name}' catalog which does not allow installation. "
                f"Use --from with the preset's repository URL instead."
            )

        download_url = pack_info.get("download_url")
        if not download_url:
            raise PresetError(
                f"Preset '{pack_id}' has no download URL"
            )

        from urllib.parse import urlparse

        parsed = urlparse(download_url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and is_localhost
        ):
            raise PresetError(
                f"Preset download URL must use HTTPS: {download_url}"
            )

        if target_dir is None:
            target_dir = self.cache_dir / "downloads"
        target_dir.mkdir(parents=True, exist_ok=True)

        version = pack_info.get("version", "unknown")
        zip_filename = f"{pack_id}-{version}.zip"
        zip_path = target_dir / zip_filename

        try:
            with urllib.request.urlopen(download_url, timeout=60) as response:
                zip_data = response.read()

            zip_path.write_bytes(zip_data)
            return zip_path

        except urllib.error.URLError as e:
            raise PresetError(
                f"Failed to download preset from {download_url}: {e}"
            )
        except IOError as e:
            raise PresetError(f"Failed to save preset ZIP: {e}")