def main(select_build, skip_build, select_tag, verbose, very_verbose):
    if verbose:
        logger.setLevel(logging.DEBUG)
    if very_verbose:
        logger.setLevel(TRACE)
        handler.setLevel(TRACE)
    check_conda_lock_version()
    check_conda_version()

    filtered_build_metadata_list = [
        each for each in build_metadata_list if re.search(select_build, each["name"])
    ]
    if select_tag is not None:
        filtered_build_metadata_list = [
            each for each in build_metadata_list if each["tag"] == select_tag
        ]
    if skip_build is not None:
        filtered_build_metadata_list = [
            each
            for each in filtered_build_metadata_list
            if not re.search(skip_build, each["name"])
        ]

    selected_build_info = "\n".join(
        f"  - {each['name']}, type: {each['type']}, tag: {each['tag']}"
        for each in filtered_build_metadata_list
    )
    selected_build_message = (
        f"# {len(filtered_build_metadata_list)} selected builds\n{selected_build_info}"
    )
    logger.info(selected_build_message)

    filtered_conda_build_metadata_list = [
        each for each in filtered_build_metadata_list if each["type"] == "conda"
    ]

    if filtered_conda_build_metadata_list:
        logger.info("# Writing conda environments")
        write_all_conda_environments(filtered_conda_build_metadata_list)
        logger.info("# Writing conda lock files")
        write_all_conda_lock_files(filtered_conda_build_metadata_list)

    filtered_pip_build_metadata_list = [
        each for each in filtered_build_metadata_list if each["type"] == "pip"
    ]
    if filtered_pip_build_metadata_list:
        logger.info("# Writing pip requirements")
        write_all_pip_requirements(filtered_pip_build_metadata_list)
        logger.info("# Writing pip lock files")
        write_all_pip_lock_files(filtered_pip_build_metadata_list)