def _extract_zip_no_root(self, zip_path, extract_to, root_dir):
        self.logger.info(f"[MinerU] Extract zip: zip_path={zip_path}, extract_to={extract_to}, root_hint={root_dir}")
        base_dir = Path(extract_to).resolve()
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            members = zip_ref.infolist()
            if not root_dir:
                if members and members[0].filename.endswith("/"):
                    root_dir = members[0].filename
                else:
                    root_dir = None
            if root_dir:
                root_dir = root_dir.replace("\\", "/")
                if not root_dir.endswith("/"):
                    root_dir += "/"

            for member in members:
                if member.flag_bits & 0x1:
                    raise RuntimeError(f"[MinerU] Encrypted zip entry not supported: {member.filename}")
                if self._is_zipinfo_symlink(member):
                    raise RuntimeError(f"[MinerU] Symlink zip entry not supported: {member.filename}")

                name = member.filename.replace("\\", "/")
                if root_dir and name == root_dir:
                    self.logger.info("[MinerU] Ignore root folder...")
                    continue
                if root_dir and name.startswith(root_dir):
                    name = name[len(root_dir) :]
                if not name:
                    continue
                if name.startswith("/") or name.startswith("//") or re.match(r"^[A-Za-z]:", name):
                    raise RuntimeError(f"[MinerU] Unsafe zip path (absolute): {member.filename}")

                parts = [p for p in name.split("/") if p not in ("", ".")]
                if any(p == ".." for p in parts):
                    raise RuntimeError(f"[MinerU] Unsafe zip path (traversal): {member.filename}")

                rel_path = os.path.join(*parts) if parts else ""
                dest_path = (Path(extract_to) / rel_path).resolve(strict=False)
                if dest_path != base_dir and base_dir not in dest_path.parents:
                    raise RuntimeError(f"[MinerU] Unsafe zip path (escape): {member.filename}")

                if member.is_dir():
                    os.makedirs(dest_path, exist_ok=True)
                    continue

                os.makedirs(dest_path.parent, exist_ok=True)
                with zip_ref.open(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)