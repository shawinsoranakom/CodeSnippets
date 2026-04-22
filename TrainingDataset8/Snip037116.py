def main():
    subprocess_args = parse_args()
    (ROOT_DIR / "frontend" / "test_results").mkdir(parents=True, exist_ok=True)

    in_container_working_directory = get_container_cwd()
    compose_file = str(E2E_DIR / "docker-compose.yml")

    docker_compose_args = [
        "docker-compose",
        f"--file={compose_file}",
        "run",
        "--rm",
        "--name=streamlit_e2e_tests",
        f"--workdir={in_container_working_directory}",
        "streamlit_e2e_tests",
        *subprocess_args,
    ]
    try:
        subprocess.run(docker_compose_args, check=True)
    except subprocess.CalledProcessError as ex:
        sys.exit(ex.returncode)