def test_docker_status_to_sandbox_status(self, service):
        """Test Docker status to SandboxStatus conversion."""
        # Test all mappings
        assert (
            service._docker_status_to_sandbox_status('running') == SandboxStatus.RUNNING
        )
        assert (
            service._docker_status_to_sandbox_status('paused') == SandboxStatus.PAUSED
        )
        assert (
            service._docker_status_to_sandbox_status('exited') == SandboxStatus.PAUSED
        )
        assert (
            service._docker_status_to_sandbox_status('created')
            == SandboxStatus.STARTING
        )
        assert (
            service._docker_status_to_sandbox_status('restarting')
            == SandboxStatus.STARTING
        )
        assert (
            service._docker_status_to_sandbox_status('removing')
            == SandboxStatus.MISSING
        )
        assert service._docker_status_to_sandbox_status('dead') == SandboxStatus.ERROR
        assert (
            service._docker_status_to_sandbox_status('unknown') == SandboxStatus.ERROR
        )