async def main():
	"""Run all tasks in parallel using subprocesses"""
	semaphore = asyncio.Semaphore(MAX_PARALLEL)

	print(f'Found task files: {TASK_FILES}')

	if not TASK_FILES:
		print('No task files found!')
		return 0, 0

	# Run all tasks in parallel subprocesses
	tasks = [run_task_subprocess(task_file, semaphore) for task_file in TASK_FILES]
	results = await asyncio.gather(*tasks)

	passed = sum(1 for r in results if r['success'])
	total = len(results)

	print('\n' + '=' * 60)
	print(f'{"RESULTS":^60}\n')

	# Prepare table data
	headers = ['Task', 'Success', 'Reason']
	rows = []
	for r in results:
		status = '✅' if r['success'] else '❌'
		rows.append([r['file'], status, r['explanation']])

	# Calculate column widths
	col_widths = [max(len(str(row[i])) for row in ([headers] + rows)) for i in range(3)]

	# Print header
	header_row = ' | '.join(headers[i].ljust(col_widths[i]) for i in range(3))
	print(header_row)
	print('-+-'.join('-' * w for w in col_widths))

	# Print rows
	for row in rows:
		print(' | '.join(str(row[i]).ljust(col_widths[i]) for i in range(3)))

	print('\n' + '=' * 60)
	print(f'\n{"SCORE":^60}')
	print(f'\n{"=" * 60}\n')
	print(f'\n{"*" * 10}  {passed}/{total} PASSED  {"*" * 10}\n')
	print('=' * 60 + '\n')

	# Output results for GitHub Actions
	print(f'PASSED={passed}')
	print(f'TOTAL={total}')

	# Output detailed results as JSON for GitHub Actions
	detailed_results = []
	for r in results:
		detailed_results.append(
			{
				'task': r['file'].replace('.yaml', ''),
				'success': r['success'],
				'reason': r['explanation'],
			}
		)

	print('DETAILED_RESULTS=' + json.dumps(detailed_results))

	return passed, total