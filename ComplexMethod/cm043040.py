def read_baseline():
    """Read baseline performance metrics"""
    with open('performance_baseline.txt', 'r') as f:
        content = f.read()

    # Extract key metrics
    metrics = {}
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Total Time:' in line:
            metrics['total_time'] = float(line.split(':')[1].strip().split()[0])
        elif 'Memory Used:' in line:
            metrics['memory_mb'] = float(line.split(':')[1].strip().split()[0])
        elif 'validate_coverage:' in line and i+1 < len(lines) and 'Avg Time:' in lines[i+2]:
            metrics['validate_coverage_ms'] = float(lines[i+2].split(':')[1].strip().split()[0])
        elif 'select_links:' in line and i+1 < len(lines) and 'Avg Time:' in lines[i+2]:
            metrics['select_links_ms'] = float(lines[i+2].split(':')[1].strip().split()[0])
        elif 'calculate_confidence:' in line and i+1 < len(lines) and 'Avg Time:' in lines[i+2]:
            metrics['calculate_confidence_ms'] = float(lines[i+2].split(':')[1].strip().split()[0])

    return metrics