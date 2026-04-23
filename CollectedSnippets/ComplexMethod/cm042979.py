async def test_docker_components():
    """Test Docker utilities, registry, and image building.

    This function tests the core Docker components before running the browser tests.
    It validates DockerRegistry, DockerUtils, and builds test images to ensure
    everything is functioning correctly.
    """
    logger.info("Testing Docker components", tag="SETUP")

    # Create a test registry directory
    registry_dir = os.path.join(os.path.dirname(__file__), "test_registry")
    registry_file = os.path.join(registry_dir, "test_registry.json")
    os.makedirs(registry_dir, exist_ok=True)

    try:
        # 1. Test DockerRegistry
        logger.info("Testing DockerRegistry...", tag="SETUP")
        registry = DockerRegistry(registry_file)

        # Test saving and loading registry
        test_container_id = "test-container-123"
        registry.register_container(test_container_id, 9876, "test-hash-123")
        registry.save()

        # Create a new registry instance that loads from the file
        registry2 = DockerRegistry(registry_file)
        port = registry2.get_container_host_port(test_container_id)
        hash_value = registry2.get_container_config_hash(test_container_id)

        if port != 9876 or hash_value != "test-hash-123":
            logger.error("DockerRegistry persistence failed", tag="SETUP")
            return False

        # Clean up test container from registry
        registry2.unregister_container(test_container_id)
        logger.success("DockerRegistry works correctly", tag="SETUP")

        # 2. Test DockerUtils
        logger.info("Testing DockerUtils...", tag="SETUP")

        # Test port detection
        in_use = docker_utils.is_port_in_use(22)  # SSH port is usually in use
        logger.info(f"Port 22 in use: {in_use}", tag="SETUP")

        # Get next available port
        available_port = docker_utils.get_next_available_port(9000)
        logger.info(f"Next available port: {available_port}", tag="SETUP")

        # Test config hash generation
        config_dict = {"mode": "connect", "headless": True}
        config_hash = docker_utils.generate_config_hash(config_dict)
        logger.info(f"Generated config hash: {config_hash[:8]}...", tag="SETUP")

        # 3. Test Docker is available
        logger.info("Checking Docker availability...", tag="SETUP")
        if not await check_docker_available():
            logger.error("Docker is not available - cannot continue tests", tag="SETUP")
            return False

        # 4. Test building connect image
        logger.info("Building connect mode Docker image...", tag="SETUP")
        connect_image = await docker_utils.ensure_docker_image_exists(None, "connect")
        if not connect_image:
            logger.error("Failed to build connect mode image", tag="SETUP")
            return False
        logger.success(f"Successfully built connect image: {connect_image}", tag="SETUP")

        # 5. Test building launch image
        logger.info("Building launch mode Docker image...", tag="SETUP")
        launch_image = await docker_utils.ensure_docker_image_exists(None, "launch")
        if not launch_image:
            logger.error("Failed to build launch mode image", tag="SETUP")
            return False
        logger.success(f"Successfully built launch image: {launch_image}", tag="SETUP")

        # 6. Test creating and removing container
        logger.info("Testing container creation and removal...", tag="SETUP")
        container_id = await docker_utils.create_container(
            image_name=launch_image,
            host_port=available_port,
            container_name="crawl4ai-test-container"
        )

        if not container_id:
            logger.error("Failed to create test container", tag="SETUP")
            return False

        logger.info(f"Created test container: {container_id[:12]}", tag="SETUP")

        # Verify container is running
        running = await docker_utils.is_container_running(container_id)
        if not running:
            logger.error("Test container is not running", tag="SETUP")
            await docker_utils.remove_container(container_id)
            return False

        # Test commands in container
        logger.info("Testing command execution in container...", tag="SETUP")
        returncode, stdout, stderr = await docker_utils.exec_in_container(
            container_id, ["ls", "-la", "/"]
        )

        if returncode != 0:
            logger.error(f"Command execution failed: {stderr}", tag="SETUP")
            await docker_utils.remove_container(container_id)
            return False

        # Verify Chrome is installed in the container
        returncode, stdout, stderr = await docker_utils.exec_in_container(
            container_id, ["which", "chromium"]
        )

        if returncode != 0:
            logger.error("Chrome not found in container", tag="SETUP")
            await docker_utils.remove_container(container_id)
            return False

        chrome_path = stdout.strip()
        logger.info(f"Chrome found at: {chrome_path}", tag="SETUP")

        # Test Chrome version
        returncode, stdout, stderr = await docker_utils.exec_in_container(
            container_id, ["chromium", "--version"]
        )

        if returncode != 0:
            logger.error(f"Failed to get Chrome version: {stderr}", tag="SETUP")
            await docker_utils.remove_container(container_id)
            return False

        logger.info(f"Chrome version: {stdout.strip()}", tag="SETUP")

        # Remove test container
        removed = await docker_utils.remove_container(container_id)
        if not removed:
            logger.error("Failed to remove test container", tag="SETUP")
            return False

        logger.success("Test container removed successfully", tag="SETUP")

        # All components tested successfully
        logger.success("All Docker components tested successfully", tag="SETUP")
        return True

    except Exception as e:
        logger.error(f"Docker component tests failed: {str(e)}", tag="SETUP")
        return False
    finally:
        # Clean up registry test directory
        if os.path.exists(registry_dir):
            shutil.rmtree(registry_dir)