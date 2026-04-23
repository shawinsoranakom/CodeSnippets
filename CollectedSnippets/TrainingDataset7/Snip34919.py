def change_loader_patterns(patterns):
    original_patterns = DiscoverRunner.test_loader.testNamePatterns
    DiscoverRunner.test_loader.testNamePatterns = patterns
    try:
        yield
    finally:
        DiscoverRunner.test_loader.testNamePatterns = original_patterns