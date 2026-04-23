def pytest_runtestloop(session):
    """
    This pytest plugin allows us to pre-install external dependencies that are usually lazy-loaded by the services.
    This helps us surface download issues earlier.
    This is not needed if we are running the test against an external instance, as it installs the dependencies on the
    runner running the tests.
    """
    if not session.items:
        return

    if session.config.option.collectonly:
        return

    if test_config.TEST_SKIP_LOCALSTACK_START:
        return

    from localstack.testing.aws.util import is_aws_cloud

    if is_aws_cloud() and not test_config.TEST_FORCE_LOCALSTACK_START:
        return

    # second pytest lifecycle hook (before test runner starts)
    test_init_functions = set()

    # collect test classes
    test_classes = set()
    for item in session.items:
        if item.parent and item.parent.cls:
            test_classes.add(item.parent.cls)
        # OpenSearch/Elasticsearch are pytests, not unit test classes, so we check based on the item parent's name.
        # Any pytests that rely on opensearch/elasticsearch must be special-cased by adding them to the list below
        parent_name = str(item.parent).lower()
        if any(opensearch_test in parent_name for opensearch_test in ["opensearch", "firehose"]):
            from tests.aws.services.opensearch.test_opensearch import (
                install_async as opensearch_install_async,
            )

            test_init_functions.add(opensearch_install_async)

        if any(es_test in parent_name for es_test in ["elasticsearch", "firehose"]):
            from tests.aws.services.es.test_es import install_async as es_install_async

            test_init_functions.add(es_install_async)

        if "transcribe" in parent_name:
            from tests.aws.services.transcribe.test_transcribe import (
                install_async as transcribe_install_async,
            )

            test_init_functions.add(transcribe_install_async)

    for fn in test_init_functions:
        fn()