def generate_report(self, result: VerificationResult) -> str:
        """Generate a verification report."""
        lines = [
            "",
            "=" * 60,
            "Migration Verification Report",
            "=" * 60,
            f"ES Index:  {result.es_index}",
            f"OB Table:  {result.ob_table}",
        ]

        lines.extend([
            "",
            "Document Counts:",
            f"  Elasticsearch: {result.es_count:,}",
            f"  OceanBase:     {result.ob_count:,}",
            f"  Difference:    {result.count_diff:,}",
            f"  Match:         {'Yes' if result.count_match else 'No'}",
            "",
            "Sample Verification:",
            f"  Sample Size:   {result.sample_size}",
            f"  Verified:      {result.samples_verified}",
            f"  Matched:       {result.samples_matched}",
            f"  Match Rate:    {result.sample_match_rate:.2%}",
            "",
        ])

        if result.missing_in_ob:
            lines.append(f"Missing in OceanBase ({len(result.missing_in_ob)}):")
            for doc_id in result.missing_in_ob[:5]:
                lines.append(f"  - {doc_id}")
            if len(result.missing_in_ob) > 5:
                lines.append(f"  ... and {len(result.missing_in_ob) - 5} more")
            lines.append("")

        if result.data_mismatches:
            lines.append(f"Data Mismatches ({len(result.data_mismatches)}):")
            for mismatch in result.data_mismatches[:3]:
                lines.append(f"  - ID: {mismatch['id']}")
                for diff in mismatch.get("differences", [])[:2]:
                    lines.append(f"    {diff['field']}: ES={diff['es_value']}, OB={diff['ob_value']}")
            if len(result.data_mismatches) > 3:
                lines.append(f"  ... and {len(result.data_mismatches) - 3} more")
            lines.append("")

        lines.extend([
            "=" * 60,
            f"Result: {'PASSED' if result.passed else 'FAILED'}",
            result.message,
            "=" * 60,
            "",
        ])

        return "\n".join(lines)