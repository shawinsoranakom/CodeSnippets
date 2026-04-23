async def load_skills_from_agent_server(
    agent_server_url: str,
    session_api_key: str | None,
    project_dir: str,
    org_config: OrgConfig | None = None,
    sandbox_config: SandboxConfig | None = None,
    load_public: bool = True,
    load_user: bool = True,
    load_project: bool = True,
    load_org: bool = True,
) -> list[Skill]:
    """Load all skills from the agent-server.

    This function makes a single API call to the agent-server's /api/skills
    endpoint to load and merge skills from all configured sources.

    Args:
        agent_server_url: URL of the agent server (e.g., 'http://localhost:8000')
        session_api_key: Session API key for authentication (optional)
        project_dir: Workspace directory path for project skills
        org_config: Organization skills configuration (optional)
        sandbox_config: Sandbox skills configuration (optional)
        load_public: Whether to load public skills (default: True)
        load_user: Whether to load user skills (default: True)
        load_project: Whether to load project skills (default: True)
        load_org: Whether to load organization skills (default: True)

    Returns:
        List of Skill objects merged from all sources.
        Returns empty list on error.
    """
    try:
        # Build request payload
        payload = {
            'load_public': load_public,
            'load_user': load_user,
            'load_project': load_project,
            'load_org': load_org,
            'project_dir': project_dir,
            'org_config': org_config.model_dump() if org_config else None,
            'sandbox_config': sandbox_config.model_dump() if sandbox_config else None,
        }

        # Build headers
        headers = {'Content-Type': 'application/json'}
        if session_api_key:
            headers['X-Session-API-Key'] = session_api_key

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{agent_server_url}/api/skills',
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()

            data = response.json()

        # Convert response to Skill objects
        skills: list[Skill] = []
        for skill_data_dict in data.get('skills', []):
            try:
                skill_info = SkillInfo.model_validate(skill_data_dict)
                skill = _convert_skill_info_to_skill(skill_info)
                skills.append(skill)
            except Exception as e:
                skill_name = (
                    skill_data_dict.get('name', 'unknown')
                    if isinstance(skill_data_dict, dict)
                    else 'unknown'
                )
                _logger.warning(f'Failed to convert skill {skill_name}: {e}')

        sources = data.get('sources', {})
        _logger.info(
            f'Loaded {len(skills)} skills from agent-server: '
            f'sources={sources}, names={[s.name for s in skills]}'
        )

        return skills

    except httpx.HTTPStatusError as e:
        _logger.warning(
            f'Agent-server returned error status {e.response.status_code}: '
            f'{e.response.text}'
        )
        return []
    except httpx.RequestError as e:
        _logger.warning(f'Failed to connect to agent-server: {e}')
        return []
    except Exception as e:
        _logger.warning(f'Failed to load skills from agent-server: {e}')
        return []