def load_microagents_from_dir(
    microagent_dir: Union[str, Path],
) -> tuple[dict[str, RepoMicroagent], dict[str, KnowledgeMicroagent]]:
    """Load all microagents from the given directory.

    Note, legacy repo instructions will not be loaded here.

    Args:
        microagent_dir: Path to the microagents directory (e.g. .openhands/microagents)

    Returns:
        Tuple of (repo_agents, knowledge_agents) dictionaries
    """
    if isinstance(microagent_dir, str):
        microagent_dir = Path(microagent_dir)

    repo_agents = {}
    knowledge_agents = {}

    # Load all agents from microagents directory
    logger.debug(f'Loading agents from {microagent_dir}')

    # Always check for .cursorrules and AGENTS.md files in repo root, regardless of whether microagents_dir exists
    special_files = []
    repo_root = microagent_dir.parent.parent

    # Check for .cursorrules
    if (repo_root / '.cursorrules').exists():
        special_files.append(repo_root / '.cursorrules')

    # Check for AGENTS.md (case-insensitive)
    for agents_filename in ['AGENTS.md', 'agents.md', 'AGENT.md', 'agent.md']:
        agents_path = repo_root / agents_filename
        if agents_path.exists():
            special_files.append(agents_path)
            break  # Only add the first one found to avoid duplicates

    # Collect .md files from microagents directory if it exists
    md_files = []
    if microagent_dir.exists():
        md_files = [f for f in microagent_dir.rglob('*.md') if f.name != 'README.md']

    # Process all files in one loop
    for file in chain(special_files, md_files):
        try:
            agent = BaseMicroagent.load(file, microagent_dir)
            if isinstance(agent, RepoMicroagent):
                repo_agents[agent.name] = agent
            elif isinstance(agent, KnowledgeMicroagent):
                # Both KnowledgeMicroagent and TaskMicroagent go into knowledge_agents
                knowledge_agents[agent.name] = agent
        except MicroagentValidationError as e:
            # For validation errors, include the original exception
            error_msg = f'Error loading microagent from {file}: {str(e)}'
            raise MicroagentValidationError(error_msg) from e
        except Exception as e:
            # For other errors, wrap in a ValueError with detailed message
            error_msg = f'Error loading microagent from {file}: {str(e)}'
            raise ValueError(error_msg) from e

    logger.debug(
        f'Loaded {len(repo_agents) + len(knowledge_agents)} microagents: '
        f'{[*repo_agents.keys(), *knowledge_agents.keys()]}'
    )
    return repo_agents, knowledge_agents