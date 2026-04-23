async def run_task_subprocess(task_file, semaphore):
	"""Run a task in a separate subprocess"""
	async with semaphore:
		try:
			# Set environment to reduce noise in subprocess
			env = os.environ.copy()
			env['PYTHONPATH'] = os.pathsep.join(sys.path)

			proc = await asyncio.create_subprocess_exec(
				sys.executable,
				__file__,
				'--task',
				task_file,
				stdout=asyncio.subprocess.PIPE,
				stderr=asyncio.subprocess.PIPE,
				env=env,
			)
			stdout, stderr = await proc.communicate()

			if proc.returncode == 0:
				try:
					# Parse JSON result from subprocess
					stdout_text = stdout.decode().strip()
					stderr_text = stderr.decode().strip()

					# Display subprocess debug logs
					if stderr_text:
						print(f'[SUBPROCESS {os.path.basename(task_file)}] Debug output:')
						for line in stderr_text.split('\n'):
							if line.strip():
								print(f'  {line}')

					# Find the JSON line (should be the last line that starts with {)
					lines = stdout_text.split('\n')
					json_line = None
					for line in reversed(lines):
						line = line.strip()
						if line.startswith('{') and line.endswith('}'):
							json_line = line
							break

					if json_line:
						result = json.loads(json_line)
						print(f'[PARENT] Task {os.path.basename(task_file)} completed: {result["success"]}')
					else:
						raise ValueError(f'No JSON found in output: {stdout_text}')

				except (json.JSONDecodeError, ValueError) as e:
					result = {
						'file': os.path.basename(task_file),
						'success': False,
						'explanation': f'Failed to parse subprocess result: {str(e)[:100]}',
					}
					print(f'[PARENT] Task {os.path.basename(task_file)} failed to parse: {str(e)}')
					print(f'[PARENT] Full stdout was: {stdout.decode()[:500]}')
			else:
				stderr_text = stderr.decode().strip()
				result = {
					'file': os.path.basename(task_file),
					'success': False,
					'explanation': f'Subprocess failed (code {proc.returncode}): {stderr_text[:200]}',
				}
				print(f'[PARENT] Task {os.path.basename(task_file)} subprocess failed with code {proc.returncode}')
				if stderr_text:
					print(f'[PARENT] stderr: {stderr_text[:1000]}')
				stdout_text = stdout.decode().strip()
				if stdout_text:
					print(f'[PARENT] stdout: {stdout_text[:1000]}')
		except Exception as e:
			result = {
				'file': os.path.basename(task_file),
				'success': False,
				'explanation': f'Failed to start subprocess: {str(e)}',
			}
			print(f'[PARENT] Failed to start subprocess for {os.path.basename(task_file)}: {str(e)}')

		return result