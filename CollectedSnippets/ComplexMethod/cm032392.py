def _collect_tool_artifact_markdown(self, existing_text: str = "") -> str:
        md_parts = []
        for tool_obj in self.tools.values():
            if not hasattr(tool_obj, "_param") or not hasattr(tool_obj._param, "outputs"):
                continue
            artifacts_meta = tool_obj._param.outputs.get("_ARTIFACTS", {})
            artifacts = artifacts_meta.get("value") if isinstance(artifacts_meta, dict) else None
            if not artifacts:
                continue
            for art in artifacts:
                if not isinstance(art, dict):
                    continue
                url = art.get("url", "")
                if url and (f"![]({url})" in existing_text or f"![{art.get('name', '')}]({url})" in existing_text):
                    continue
                if art.get("mime_type", "").startswith("image/"):
                    md_parts.append(f"![{art['name']}]({url})")
                else:
                    md_parts.append(f"[Download {art['name']}]({url})")
        return "\n\n".join(md_parts)