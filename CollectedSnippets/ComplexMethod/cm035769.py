def test_multiple_volumes():
    """Test that multiple volumes are correctly processed."""
    import os

    from openhands.runtime.impl.docker.docker_runtime import DockerRuntime

    # Create a DockerRuntime instance with a mock config
    runtime = DockerRuntime.__new__(DockerRuntime)
    runtime.config = MagicMock()
    runtime.config.sandbox.volumes = '/host/path1:/container/path1,/host/path2:/container/path2,/host/path3:/container/path3:ro'
    runtime.config.workspace_mount_path = '/host/path1'
    runtime.config.workspace_mount_path_in_sandbox = '/container/path1'

    # Call the actual method that processes volumes
    volumes = runtime._process_volumes()

    # Assert that all mounts were processed correctly
    assert len(volumes) == 3
    assert volumes[os.path.abspath('/host/path1')]['bind'] == '/container/path1'
    assert volumes[os.path.abspath('/host/path1')]['mode'] == 'rw'
    assert volumes[os.path.abspath('/host/path2')]['bind'] == '/container/path2'
    assert volumes[os.path.abspath('/host/path2')]['mode'] == 'rw'
    assert volumes[os.path.abspath('/host/path3')]['bind'] == '/container/path3'
    assert volumes[os.path.abspath('/host/path3')]['mode'] == 'ro'