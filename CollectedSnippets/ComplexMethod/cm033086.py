def _extract_content_from_zip(self, zip_path: str) -> list[dict[str, Any]]:
        """Extract parsing results from downloaded ZIP file"""
        results = []

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                members = zip_file.infolist()
                for member in members:
                    name = member.filename.replace("\\", "/")
                    if member.is_dir():
                        continue
                    if member.flag_bits & 0x1:
                        raise RuntimeError(f"[TCADP] Encrypted zip entry not supported: {member.filename}")
                    if self._is_zipinfo_symlink(member):
                        raise RuntimeError(f"[TCADP] Symlink zip entry not supported: {member.filename}")
                    if name.startswith("/") or name.startswith("//") or re.match(r"^[A-Za-z]:", name):
                        raise RuntimeError(f"[TCADP] Unsafe zip path (absolute): {member.filename}")
                    parts = [p for p in name.split("/") if p not in ("", ".")]
                    if any(p == ".." for p in parts):
                        raise RuntimeError(f"[TCADP] Unsafe zip path (traversal): {member.filename}")

                    if not (name.endswith(".json") or name.endswith(".md")):
                        continue

                    with zip_file.open(member) as f:
                        if name.endswith(".json"):
                            data = json.load(f)
                            if isinstance(data, list):
                                results.extend(data)
                            else:
                                results.append(data)
                        else:
                            content = f.read().decode("utf-8")
                            results.append({"type": "text", "content": content, "file": name})

        except Exception as e:
            self.logger.error(f"[TCADP] Failed to extract ZIP file content: {e}")

        return results