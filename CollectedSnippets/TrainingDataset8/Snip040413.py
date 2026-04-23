def _can_run_streamlit(command_list):
    result = subprocess.run(command_list, stdout=subprocess.DEVNULL)
    return result.returncode == 0