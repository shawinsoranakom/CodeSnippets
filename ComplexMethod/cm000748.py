async def update_check_run(
        credentials: GithubCredentials,
        repo_url: str,
        check_run_id: int,
        status: ChecksStatus,
        conclusion: Optional[ChecksConclusion] = None,
        output_title: Optional[str] = None,
        output_summary: Optional[str] = None,
        output_text: Optional[str] = None,
    ) -> dict:
        api = get_api(credentials)

        class UpdateCheckRunData(BaseModel):
            status: str
            conclusion: Optional[str] = None
            output: Optional[dict[str, str]] = None

        data = UpdateCheckRunData(
            status=status.value,
        )

        if conclusion:
            data.conclusion = conclusion.value

        if output_title or output_summary or output_text:
            output_data = {
                "title": output_title or "",
                "summary": output_summary or "",
                "text": output_text or "",
            }
            data.output = output_data

        check_run_url = f"{repo_url}/check-runs/{check_run_id}"
        response = await api.patch(
            check_run_url, data=data.model_dump_json(exclude_none=True)
        )
        result = response.json()

        return {
            "id": result["id"],
            "html_url": result["html_url"],
            "status": result["status"],
            "conclusion": result.get("conclusion"),
        }