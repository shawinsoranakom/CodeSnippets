async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from .pa_provider import get_workspace_dir

        rel_path = arguments.get("path", "") or ""
        recursive = bool(arguments.get("recursive", False))

        workspace = get_workspace_dir()
        try:
            target = (workspace / rel_path).resolve() if rel_path else workspace.resolve()
            if not str(target).startswith(str(workspace.resolve())):
                return {"error": "Access outside the workspace is not allowed"}
            if self.safe_mode and target == workspace.resolve():
                return {"error": "Listing the workspace root directory is not allowed in safe mode"}
            if not target.exists():
                return {"error": f"Directory not found: {rel_path or '/'}"}
            if not target.is_dir():
                return {"error": f"Path is not a directory: {rel_path}"}

            entries = []
            skipped = 0
            iterator = target.rglob("*") if recursive else target.iterdir()
            for entry in sorted(iterator):
                try:
                    rel = str(entry.relative_to(workspace))
                    info: Dict[str, Any] = {
                        "path": rel,
                        "type": "file" if entry.is_file() else "directory",
                    }
                    if entry.is_file():
                        info["size"] = entry.stat().st_size
                    entries.append(info)
                except Exception:
                    skipped += 1
                    continue

            result: Dict[str, Any] = {
                "workspace": "" if self.safe_mode else str(workspace),
                "path": rel_path or "/",
                "entries": entries,
                "count": len(entries),
            }
            if skipped:
                result["skipped"] = skipped
            return result
        except Exception as exc:
            return {"error": f"List failed: {exc}"}