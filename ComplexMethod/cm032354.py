def _process_execution_result(
        self,
        stdout: str,
        stderr: str | None,
        source: str,
        artifacts: list | None = None,
        execution_metadata: dict | None = None,
    ):
        has_structured_result = bool((execution_metadata or {}).get("result_present") is True)
        resolved_value, used_stdout_fallback = self._resolve_execution_result_value(stdout, execution_metadata)

        if stderr and not has_structured_result and not artifacts and not str(stdout or "").strip():
            self.set_output("_ERROR", stderr)
            return self.output()

        # Clear any stale error from previous runs or base class initialization
        self.set_output("_ERROR", "")

        if stderr:
            logging.warning(f"[CodeExec]: stderr (non-fatal): {stderr[:500]}")

        if used_stdout_fallback and str(stdout or "").strip():
            logging.warning("[CodeExec]: Falling back to stdout deserialization because no structured result metadata was provided")

        logging.info(f"[CodeExec]: {source} -> {resolved_value}")
        content_parts = []
        base_content = self._apply_business_output(resolved_value)
        if base_content:
            content_parts.append(base_content)

        if artifacts:
            artifact_urls = self._upload_artifacts(artifacts)
            self.set_output("_ARTIFACTS", artifact_urls or None)
            attachment_text = self._build_attachment_content(artifacts, artifact_urls)
            self.set_output("_ATTACHMENT_CONTENT", attachment_text)
            if attachment_text:
                content_parts.append(attachment_text)
        else:
            self.set_output("_ARTIFACTS", None)
            self.set_output("_ATTACHMENT_CONTENT", "")

        self.set_output("content", "\n\n".join([part for part in content_parts if part]).strip())

        return self.output()