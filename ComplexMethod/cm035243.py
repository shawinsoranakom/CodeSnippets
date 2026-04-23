async def read_conversation_file(
    conversation_id: UUID,
    file_path: Annotated[
        str,
        Query(title='Path to the file to read within the sandbox workspace'),
    ] = '/workspace/project/PLAN.md',
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
    sandbox_service: SandboxService = sandbox_service_dependency,
    sandbox_spec_service: SandboxSpecService = sandbox_spec_service_dependency,
) -> str:
    """Read a file from a specific conversation's sandbox workspace.

    Returns the content of the file at the specified path if it exists, otherwise returns an empty string.

    Args:
        conversation_id: The UUID of the conversation
        file_path: Path to the file to read within the sandbox workspace

    Returns:
        The content of the file or an empty string if the file doesn't exist
    """
    # Get the conversation info
    conversation = await app_conversation_service.get_app_conversation(conversation_id)
    if not conversation:
        return ''

    # Get the sandbox info
    sandbox = await sandbox_service.get_sandbox(conversation.sandbox_id)
    if not sandbox or sandbox.status != SandboxStatus.RUNNING:
        return ''

    # Get the sandbox spec to find the working directory
    sandbox_spec = await sandbox_spec_service.get_sandbox_spec(sandbox.sandbox_spec_id)
    if not sandbox_spec:
        return ''

    # Get the agent server URL
    if not sandbox.exposed_urls:
        return ''

    agent_server_url = None
    for exposed_url in sandbox.exposed_urls:
        if exposed_url.name == AGENT_SERVER:
            agent_server_url = exposed_url.url
            break

    if not agent_server_url:
        return ''

    agent_server_url = replace_localhost_hostname_for_docker(agent_server_url)

    # Create remote workspace
    remote_workspace = AsyncRemoteWorkspace(
        host=agent_server_url,
        api_key=sandbox.session_api_key,
        working_dir=sandbox_spec.working_dir,
    )

    # Read the file at the specified path
    temp_file_path = None
    try:
        # Create a temporary file path to download the remote file
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
            temp_file_path = temp_file.name

        # Download the file from remote system
        result = await remote_workspace.file_download(
            source_path=file_path,
            destination_path=temp_file_path,
        )

        if result.success:
            # Read the content from the temporary file
            with open(temp_file_path, 'rb') as f:
                content = f.read()
            # Decode bytes to string
            return content.decode('utf-8')
    except Exception:
        # If there's any error reading the file, return empty string
        pass
    finally:
        # Clean up the temporary file
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
            except Exception:
                # Ignore errors during cleanup
                pass

    return ''