def _determine_result(self, result: VerificationResult):
        """Determine overall verification result."""
        # Allow small count differences (e.g., documents added during migration)
        count_tolerance = 0.01  # 1% tolerance
        count_ok = (
            result.count_match or 
            (result.es_count > 0 and result.count_diff / result.es_count <= count_tolerance)
        )

        if count_ok and result.sample_match_rate >= 0.99:
            result.passed = True
            result.message = (
                f"Verification PASSED. "
                f"ES: {result.es_count:,}, OB: {result.ob_count:,}. "
                f"Sample match rate: {result.sample_match_rate:.2%}"
            )
        elif count_ok and result.sample_match_rate >= 0.95:
            result.passed = True
            result.message = (
                f"Verification PASSED with warnings. "
                f"ES: {result.es_count:,}, OB: {result.ob_count:,}. "
                f"Sample match rate: {result.sample_match_rate:.2%}"
            )
        else:
            result.passed = False
            issues = []
            if not count_ok:
                issues.append(
                    f"Count mismatch (ES: {result.es_count}, OB: {result.ob_count}, diff: {result.count_diff})"
                )
            if result.sample_match_rate < 0.95:
                issues.append(f"Low sample match rate: {result.sample_match_rate:.2%}")
            if result.missing_in_ob:
                issues.append(f"{len(result.missing_in_ob)} documents missing in OB")
            result.message = f"Verification FAILED: {'; '.join(issues)}"