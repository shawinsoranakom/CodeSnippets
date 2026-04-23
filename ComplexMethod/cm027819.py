def execute_task(task_id, command):
    tasks_db_path = get_tasks_db_path()
    with db_connection(tasks_db_path) as conn:
        conn.execute("BEGIN EXCLUSIVE TRANSACTION")
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM task_executions 
                WHERE task_id = ? AND status = 'running'
                LIMIT 1
                """,
                (task_id,),
            )
            is_running = cursor.fetchone() is not None
            if is_running:
                print(f"WARNING: Task {task_id} is already running, skipping this execution")
                conn.commit()
                return
            cursor.execute(
                """
                INSERT INTO task_executions 
                (task_id, start_time, status)
                VALUES (?, ?, ?)
                """,
                (task_id, datetime.now().isoformat(), "running"),
            )
            execution_id = cursor.lastrowid
            conn.commit()
            if not execution_id:
                print(f"ERROR: Failed to create execution record for task {task_id}")
                return
        except Exception as e:
            conn.rollback()
            print(f"ERROR: Transaction error for task {task_id}: {str(e)}")
            return
    print(f"INFO: Starting task {task_id}: {command}")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=DEFAULT_TASK_TIMEOUT)
            if process.returncode == 0:
                status = "success"
                error_message = None
                print(f"INFO: Task {task_id} completed successfully")
            else:
                status = "failed"
                error_message = stderr if stderr else f"Process exited with code {process.returncode}"
                print(f"ERROR: Task {task_id} failed: {error_message}")
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            status = "failed"
            error_message = f"Task timed out after {DEFAULT_TASK_TIMEOUT} seconds"
            print(f"ERROR: Task {task_id} timed out")
        output = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}" if stderr else stdout
        update_task_execution(tasks_db_path, execution_id, status, error_message, output)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        update_task_last_run(tasks_db_path, task_id, timestamp)
    except Exception as e:
        print(f"ERROR: Error executing task {task_id}: {str(e)}")
        error_message = traceback.format_exc()
        update_task_execution(tasks_db_path, execution_id, "failed", error_message)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        update_task_last_run(tasks_db_path, task_id, timestamp)