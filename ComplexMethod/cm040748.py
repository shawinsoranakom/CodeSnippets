def _get_lambda_code_param(
    properties: LambdaFunctionProperties,
    _include_arch=False,
):
    # code here is mostly taken directly from legacy implementation
    code = properties.get("Code", {}).copy()

    # TODO: verify only one of "ImageUri" | "S3Bucket" | "ZipFile" is set
    zip_file = code.get("ZipFile")
    if zip_file and not _runtime_supports_inline_code(properties["Runtime"]):
        raise Exception(
            f"Runtime {properties['Runtime']} doesn't support inlining code via the 'ZipFile' property."
        )  # TODO: message not validated
    if zip_file and not is_base64(zip_file) and not is_zip_file(to_bytes(zip_file)):
        tmp_dir = new_tmp_dir()
        try:
            handler_file = get_handler_file_from_name(
                properties["Handler"], runtime=properties["Runtime"]
            )
            tmp_file = os.path.join(tmp_dir, handler_file)
            save_file(tmp_file, zip_file)

            # CloudFormation only includes cfn-response libs if an import is detected
            # TODO: add snapshots for this behavior
            # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-lambda-function-code-cfnresponsemodule.html
            if properties["Runtime"].lower().startswith("node") and (
                "require('cfn-response')" in zip_file or 'require("cfn-response")' in zip_file
            ):
                # the check if cfn-response is used is pretty simplistic and apparently based on simple string matching
                # having the import commented out will also lead to cfn-response.js being injected
                # this is added under both cfn-response.js and node_modules/cfn-response.js
                cfn_response_mod_dir = os.path.join(tmp_dir, "node_modules")
                mkdir(cfn_response_mod_dir)
                save_file(
                    os.path.join(cfn_response_mod_dir, "cfn-response.js"),
                    NODEJS_CFN_RESPONSE_CONTENT,
                )
                save_file(os.path.join(tmp_dir, "cfn-response.js"), NODEJS_CFN_RESPONSE_CONTENT)
            elif (
                properties["Runtime"].lower().startswith("python")
                and "import cfnresponse" in zip_file
            ):
                save_file(os.path.join(tmp_dir, "cfnresponse.py"), PYTHON_CFN_RESPONSE_CONTENT)

            # create zip file
            zip_file = create_zip_file(tmp_dir, get_content=True)
            code["ZipFile"] = zip_file
        finally:
            rm_rf(tmp_dir)
    if _include_arch and "Architectures" in properties:
        code["Architectures"] = properties.get("Architectures")
    return code