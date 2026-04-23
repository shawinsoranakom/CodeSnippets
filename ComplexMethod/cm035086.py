def maybe_download(model_storage_directory, url):
    # using custom model
    tar_file_name_list = [".pdiparams", ".pdiparams.info", ".pdmodel"]
    if not os.path.exists(
        os.path.join(model_storage_directory, "inference.pdiparams")
    ) or not os.path.exists(os.path.join(model_storage_directory, "inference.pdmodel")):
        assert url.endswith(".tar"), "Only supports tar compressed package"
        tmp_path = os.path.join(model_storage_directory, url.split("/")[-1])
        print("download {} to {}".format(url, tmp_path))
        os.makedirs(model_storage_directory, exist_ok=True)
        download_with_progressbar(url, tmp_path)
        with tarfile.open(tmp_path, "r") as tarObj:
            for member in tarObj.getmembers():
                filename = None
                for tar_file_name in tar_file_name_list:
                    if member.name.endswith(tar_file_name):
                        filename = "inference" + tar_file_name
                if filename is None:
                    continue
                file = tarObj.extractfile(member)
                with open(os.path.join(model_storage_directory, filename), "wb") as f:
                    f.write(file.read())
        os.remove(tmp_path)