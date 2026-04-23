def delete_folders_with_missing_results(runlogs_path: str, noconfirm: bool = False) -> None:
    deleted_folders = 0

    for task_id in os.listdir(runlogs_path):
        task_path = os.path.join(runlogs_path, task_id)

        if not os.path.isdir(task_path):
            continue

        instance = 0
        has_missing_results = False

        while True:
            instance_dir = os.path.join(task_path, str(instance))
            if not os.path.isdir(instance_dir):
                if instance == 0:
                    print(f"Empty folder: {task_path}")
                    has_missing_results = True
                break
            if not default_scorer(instance_dir):
                has_missing_results = True
                break

            instance += 1
        if has_missing_results:
            if not noconfirm:
                print(f"Missing Results in : {task_path}")
                user_confirmation = input("Press 1 to delete, anything else to skip...")
                if user_confirmation == "1":
                    shutil.rmtree(task_path)
                    print(f"Deleted folder: {task_path}")
                    deleted_folders += 1
                else:
                    print(f"Skipping folder: {task_path}")
            else:
                shutil.rmtree(task_path)
                print(f"Deleted folder: {task_path}")
                deleted_folders += 1

    print(f"Total folders deleted: {deleted_folders}")