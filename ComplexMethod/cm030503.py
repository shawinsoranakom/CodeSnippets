def _calculate_file_stats(self) -> List[FileStats]:
        """Calculate statistics for each file.

        Returns:
            List of FileStats objects sorted by total samples
        """
        file_stats = []
        for filename, line_counts in self.file_samples.items():
            # Skip special frames
            if filename in ('~', '...', '.') or filename.startswith('<') or filename.startswith('['):
                continue

            # Filter out lines with -1 (special frames)
            valid_line_counts = {line: count for line, count in line_counts.items() if line >= 0}
            if not valid_line_counts:
                continue

            # Get self samples for this file
            self_line_counts = self.file_self_samples.get(filename, {})
            valid_self_counts = {line: count for line, count in self_line_counts.items() if line >= 0}

            total_samples = sum(valid_line_counts.values())
            total_self_samples = sum(valid_self_counts.values())
            num_lines = len(valid_line_counts)
            max_samples = max(valid_line_counts.values())
            max_self_samples = max(valid_self_counts.values()) if valid_self_counts else 0
            module_name, module_type = extract_module_name(filename, self._path_info)

            file_stats.append(FileStats(
                filename=filename,
                module_name=module_name,
                module_type=module_type,
                total_samples=total_samples,
                total_self_samples=total_self_samples,
                num_lines=num_lines,
                max_samples=max_samples,
                max_self_samples=max_self_samples,
                percentage=0.0
            ))

        # Sort by total samples and calculate percentages
        file_stats.sort(key=lambda x: x.total_samples, reverse=True)
        if file_stats:
            max_total = file_stats[0].total_samples
            for stat in file_stats:
                stat.percentage = (stat.total_samples / max_total * 100) if max_total > 0 else 0

        return file_stats