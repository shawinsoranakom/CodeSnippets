def _summarize_checks(checks: dict[str, dict[str, Any]]) -> str:
	"""Generate a summary of check results."""
	ok = sum(1 for c in checks.values() if c.get('status') == 'ok')
	warning = sum(1 for c in checks.values() if c.get('status') == 'warning')
	error = sum(1 for c in checks.values() if c.get('status') == 'error')
	missing = sum(1 for c in checks.values() if c.get('status') == 'missing')

	total = len(checks)

	parts = [f'{ok}/{total} checks passed']
	if warning > 0:
		parts.append(f'{warning} warnings')
	if error > 0:
		parts.append(f'{error} errors')
	if missing > 0:
		parts.append(f'{missing} missing')

	return ', '.join(parts)