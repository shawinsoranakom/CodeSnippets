def pytest_runtestloop(session: Session):
    # avoid starting up localstack if we only collect the tests (-co / --collect-only)
    if session.config.option.collectonly:
        return

    if not session.config.option.start_localstack:
        return

    from localstack.testing.aws.util import is_aws_cloud

    if test_config.TEST_SKIP_LOCALSTACK_START:
        LOG.info("TEST_SKIP_LOCALSTACK_START is set, not starting localstack")
        return

    if is_aws_cloud():
        if not test_config.TEST_FORCE_LOCALSTACK_START:
            LOG.info("Test running against aws, not starting localstack")
            return
        LOG.info("TEST_FORCE_LOCALSTACK_START is set, a Localstack instance will be created.")

    if is_aws_cloud():
        localstack_config.DEFAULT_DELAY = 5
        localstack_config.DEFAULT_MAX_ATTEMPTS = 60

    # configure
    os.environ[ENV_INTERNAL_TEST_RUN] = "1"
    localstack_config.INCLUDE_STACK_TRACES_IN_HTTP_RESPONSE = True

    from localstack.runtime import current

    _started.set()
    runtime = current.initialize_runtime()
    # start runtime asynchronously
    threading.Thread(target=runtime.run).start()

    # wait for runtime to be ready
    if not runtime.ready.wait(timeout=120):
        raise TimeoutError("gave up waiting for runtime to be ready")