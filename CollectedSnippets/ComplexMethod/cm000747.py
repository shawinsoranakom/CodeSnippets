async def create_check_run(
        credentials: GithubCredentials,
        repo_url: str,
        name: str,
        head_sha: str,
        status: ChecksStatus,
        conclusion: Optional[ChecksConclusion] = None,
        details_url: Optional[str] = None,
        output_title: Optional[str] = None,
        output_summary: Optional[str] = None,
        output_text: Optional[str] = None,
    ) -> dict:
        api = get_api(credentials)

        class CheckRunData(BaseModel):
            name: str
            head_sha: str
            status: str
            conclusion: Optional[str] = None
            details_url: Optional[str] = None
            output: Optional[dict[str, str]] = None

        data = CheckRunData(
            name=name,
            head_sha=head_sha,
            status=status.value,
        )

        if conclusion:
            data.conclusion = conclusion.value

        if details_url:
            data.details_url = details_url

        if output_title or output_summary or output_text:
            output_data = {
                "title": output_title or "",
                "summary": output_summary or "",
                "text": output_text or "",
            }
            data.output = output_data

        check_runs_url = f"{repo_url}/check-runs"
        response = await api.post(
            check_runs_url, data=data.model_dump_json(exclude_none=True)
        )
        result = response.json()

        return {
            "id": result["id"],
            "html_url": result["html_url"],
            "status": result["status"],
        }