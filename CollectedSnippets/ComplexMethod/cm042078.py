def check_or_create_base_tag(project_path):
    # Change the current working directory to the specified project path
    os.chdir(project_path)

    # Initialize a Git repository
    subprocess.run(["git", "init"], check=True)

    # Check if the .gitignore exists. If it doesn't exist, create .gitignore and add the comment
    subprocess.run(f"echo # Ignore these files or directories > {'.gitignore'}", shell=True)

    # Check if the 'base' tag exists
    check_base_tag_cmd = ["git", "show-ref", "--verify", "--quiet", "refs/tags/base"]
    if subprocess.run(check_base_tag_cmd).returncode == 0:
        has_base_tag = True
    else:
        has_base_tag = False

    if has_base_tag:
        logger.info("Base tag exists")
        # Switch to the 'base' branch if it exists
        try:
            status = subprocess.run(["git", "status", "-s"], capture_output=True, text=True).stdout.strip()
            if status:
                subprocess.run(["git", "clean", "-df"])
            subprocess.run(["git", "checkout", "-f", "base"], check=True)
            logger.info("Switched to base branch")
        except Exception as e:
            logger.error("Failed to switch to base branch")
            raise e

    else:
        logger.info("Base tag doesn't exist.")
        # Add and commit the current code if 'base' tag doesn't exist
        add_cmd = ["git", "add", "."]
        try:
            subprocess.run(add_cmd, check=True)
            logger.info("Files added successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add files: {e}")

        commit_cmd = ["git", "commit", "-m", "Initial commit"]
        try:
            subprocess.run(commit_cmd, check=True)
            logger.info("Committed all files with the message 'Initial commit'.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e.stderr}")

        # Add 'base' tag
        add_base_tag_cmd = ["git", "tag", "base"]

        # Check if the 'git tag' command was successful
        try:
            subprocess.run(add_base_tag_cmd, check=True)
            logger.info("Added 'base' tag.")
        except Exception as e:
            logger.error("Failed to add 'base' tag.")
            raise e