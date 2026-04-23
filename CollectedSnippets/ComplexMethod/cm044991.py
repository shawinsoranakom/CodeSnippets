def download_extension(self, extension_id: str, target_dir: Optional[Path] = None) -> Path:
        """Download extension ZIP from catalog.

        Args:
            extension_id: ID of the extension to download
            target_dir: Directory to save ZIP file (defaults to temp directory)

        Returns:
            Path to downloaded ZIP file

        Raises:
            ExtensionError: If extension not found or download fails
        """
        import urllib.request
        import urllib.error

        # Get extension info from catalog
        ext_info = self.get_extension_info(extension_id)
        if not ext_info:
            raise ExtensionError(f"Extension '{extension_id}' not found in catalog")

        # Bundled extensions without a download URL must be installed locally
        if ext_info.get("bundled") and not ext_info.get("download_url"):
            raise ExtensionError(
                f"Extension '{extension_id}' is bundled with spec-kit and has no download URL. "
                f"It should be installed from the local package. "
                f"Try reinstalling: {REINSTALL_COMMAND}"
            )

        download_url = ext_info.get("download_url")
        if not download_url:
            raise ExtensionError(f"Extension '{extension_id}' has no download URL")

        # Validate download URL requires HTTPS (prevent man-in-the-middle attacks)
        from urllib.parse import urlparse
        parsed = urlparse(download_url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
            raise ExtensionError(
                f"Extension download URL must use HTTPS: {download_url}"
            )

        # Determine target path
        if target_dir is None:
            target_dir = self.cache_dir / "downloads"
        target_dir.mkdir(parents=True, exist_ok=True)

        version = ext_info.get("version", "unknown")
        zip_filename = f"{extension_id}-{version}.zip"
        zip_path = target_dir / zip_filename

        # Download the ZIP file
        try:
            with urllib.request.urlopen(download_url, timeout=60) as response:
                zip_data = response.read()

            zip_path.write_bytes(zip_data)
            return zip_path

        except urllib.error.URLError as e:
            raise ExtensionError(f"Failed to download extension from {download_url}: {e}")
        except IOError as e:
            raise ExtensionError(f"Failed to save extension ZIP: {e}")