def load_with_patterns(self):
        original_test_name_patterns = self.test_loader.testNamePatterns
        self.test_loader.testNamePatterns = self.test_name_patterns
        try:
            yield
        finally:
            # Restore the original patterns.
            self.test_loader.testNamePatterns = original_test_name_patterns