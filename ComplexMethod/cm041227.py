def load_nodejs_lambda_to_s3(
    s3_client: "S3Client",
    bucket_name: str,
    key_name: str,
    code_path: str,
    additional_nodjs_packages: list[str] = None,
    additional_nodejs_packages: list[str] = None,
    additional_resources: list[str] = None,
):
    """
    Helper function to setup nodeJS Lambdas that need additional libs.
    Will create a temp-zip and upload in the s3 bucket.
    Installs additional libs and package with the zip

    :param s3_client: client for S3
    :param bucket_name: bucket name (bucket will be created)
    :param key_name: key name for the uploaded zip file
    :param code_path: the path to the source code that should be included
    :param additional_nodjs_packages: a list of strings with nodeJS packages that are required to run the lambda
    :param additional_nodejs_packages: a list of strings with nodeJS packages that are required to run the lambda
    :param additional_resources: list of path-strings to resources or internal libs that should be packaged into the lambda
    :return: None
    """
    additional_resources = additional_resources or []

    if additional_nodjs_packages:
        additional_nodejs_packages = additional_nodejs_packages or []
        additional_nodejs_packages.extend(additional_nodjs_packages)

    try:
        temp_dir = tempfile.mkdtemp()
        tmp_zip_path = os.path.join(tempfile.gettempdir(), "helper.zip")

        # Install NodeJS packages
        if additional_nodejs_packages:
            try:
                os.mkdir(os.path.join(temp_dir, "node_modules"))
                run(f"cd {temp_dir} && npm install {' '.join(additional_nodejs_packages)} ")
            except Exception as e:
                LOG.error(
                    "Could not install additional packages %s: %s", additional_nodejs_packages, e
                )

        for r in additional_resources:
            try:
                path = Path(r)
                if path.is_dir():
                    dir_name = os.path.basename(path)
                    dest_dir = os.path.join(temp_dir, dir_name)
                    shutil.copytree(path, dest_dir)
                elif path.is_file():
                    new_resource_temp_path = os.path.join(temp_dir, os.path.basename(path))
                    shutil.copy2(path, new_resource_temp_path)
            except Exception as e:
                LOG.error("Could not copy additional resources %s: %s", r, e)

        _zip_lambda_resources(
            lambda_code_path=code_path,
            handler_file_name="index.js",
            resources_dir=temp_dir,
            zip_path=tmp_zip_path,
        )
        _upload_to_s3(s3_client, bucket_name=bucket_name, key_name=key_name, file=tmp_zip_path)
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)
        if tmp_zip_path and os.path.exists(tmp_zip_path):
            os.remove(tmp_zip_path)