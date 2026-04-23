def log_and_check_result(result, tag_name="refine"):
    logger.info(result)
    logger.info(result.output)
    if "Aborting" in result.output:
        assert False
    else:
        # After running, there will be new commit
        cur_tag = subprocess.run(["git", "describe", "--tags"], capture_output=True, text=True).stdout.strip()
        if cur_tag == "base":
            assert False
        else:
            assert True
            if subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag_name}"]).returncode == 0:
                tag_name += str(int(time.time()))
            try:
                subprocess.run(["git", "tag", tag_name], check=True)
            except subprocess.CalledProcessError as e:
                raise e