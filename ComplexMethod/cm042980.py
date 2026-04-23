async def test_docker_registry_reuse():
    """Test Docker container reuse via registry.

    This tests that containers with matching configurations
    are reused rather than creating new ones.
    """
    logger.info("Testing Docker container reuse via registry", tag="TEST")

    # Create registry for this test
    registry_dir = os.path.join(os.path.dirname(__file__), "registry_reuse_test")
    registry_file = os.path.join(registry_dir, "registry.json")
    os.makedirs(registry_dir, exist_ok=True)

    manager1 = None
    manager2 = None
    container_id1 = None

    try:
        # Create identical Docker configurations with custom registry
        docker_config1 = DockerConfig(
            mode="connect",
            persistent=True,  # Keep container running after closing
            registry_file=registry_file
        )

        # Create first browser configuration
        browser_config1 = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config1
        )

        # Create first browser manager
        manager1 = BrowserManager(browser_config=browser_config1, logger=logger)

        # Start the first browser
        await manager1.start()
        logger.info("First browser started successfully", tag="TEST")

        # Get container ID from the strategy
        docker_strategy1 = manager1.strategy
        container_id1 = docker_strategy1.container_id
        logger.info(f"First browser container ID: {container_id1[:12]}", tag="TEST")

        # Close the first manager but keep container running
        await manager1.close()
        logger.info("First browser closed", tag="TEST")

        # Create second Docker configuration identical to first
        docker_config2 = DockerConfig(
            mode="connect",
            persistent=True,
            registry_file=registry_file
        )

        # Create second browser configuration
        browser_config2 = BrowserConfig(
            browser_mode="docker",
            headless=True,
            docker_config=docker_config2
        )

        # Create second browser manager
        manager2 = BrowserManager(browser_config=browser_config2, logger=logger)

        # Start the second browser - should reuse existing container
        await manager2.start()
        logger.info("Second browser started successfully", tag="TEST")

        # Get container ID from the second strategy
        docker_strategy2 = manager2.strategy
        container_id2 = docker_strategy2.container_id
        logger.info(f"Second browser container ID: {container_id2[:12]}", tag="TEST")

        # Verify container reuse
        if container_id1 == container_id2:
            logger.success("Container reuse successful - using same container!", tag="TEST")
        else:
            logger.error("Container reuse failed - new container created!", tag="TEST")

        # Clean up
        docker_strategy2.docker_config.persistent = False
        docker_strategy2.docker_config.remove_on_exit = True
        await manager2.close()
        logger.info("Second browser closed and container removed", tag="TEST")

        return container_id1 == container_id2
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Ensure cleanup
        try:
            if manager1:
                await manager1.close()
            if manager2:
                await manager2.close()
            # Make sure container is removed
            if container_id1:
                await docker_utils.remove_container(container_id1, force=True)
        except:
            pass
        return False
    finally:
        # Clean up registry directory
        if os.path.exists(registry_dir):
            shutil.rmtree(registry_dir)