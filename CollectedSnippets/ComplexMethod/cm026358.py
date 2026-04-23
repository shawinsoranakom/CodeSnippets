async def _find_pr_artifact(client: GitHubAPI, pr_number: int, head_sha: str) -> str:
    """Find the build artifact for the given PR and commit SHA.

    Returns the artifact download URL.
    """
    try:
        response = await client.generic(
            endpoint="/repos/home-assistant/frontend/actions/workflows/ci.yaml/runs",
            params={"head_sha": head_sha, "per_page": 10},
        )

        for run in response.data.get("workflow_runs", []):
            if run["status"] == "completed" and run["conclusion"] == "success":
                artifacts_response = await client.generic(
                    endpoint=f"/repos/home-assistant/frontend/actions/runs/{run['id']}/artifacts",
                )

                for artifact in artifacts_response.data.get("artifacts", []):
                    if artifact["name"] == ARTIFACT_NAME:
                        _LOGGER.info(
                            "Found artifact '%s' from CI run #%s",
                            ARTIFACT_NAME,
                            run["id"],
                        )
                        return str(artifact["archive_download_url"])

        raise HomeAssistantError(
            f"No '{ARTIFACT_NAME}' artifact found for PR #{pr_number}. "
            "Possible reasons: CI has not run yet or is running, "
            "or the build failed, or the PR artifact expired. "
            f"Check https://github.com/{GITHUB_REPO}/pull/{pr_number}/checks"
        )
    except GitHubAuthenticationException as err:
        raise HomeAssistantError(ERROR_INVALID_TOKEN) from err
    except (GitHubRatelimitException, GitHubPermissionException) as err:
        raise HomeAssistantError(ERROR_RATE_LIMIT) from err
    except GitHubException as err:
        raise HomeAssistantError(f"GitHub API error: {err}") from err