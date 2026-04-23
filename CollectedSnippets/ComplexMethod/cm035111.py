def downloadModels(self, URLs):
        # using custom model
        tar_file_name_list = [
            "inference.pdiparams",
            "inference.pdiparams.info",
            "inference.pdmodel",
            "model.pdiparams",
            "model.pdiparams.info",
            "model.pdmodel",
        ]
        model_path = os.path.join(root, "inference")
        os.makedirs(model_path, exist_ok=True)

        # download and unzip models
        for name in URLs.keys():
            url = URLs[name]
            print("Try downloading file: {}".format(url))
            tarname = url.split("/")[-1]
            tarpath = os.path.join(model_path, tarname)
            if os.path.exists(tarpath):
                print("File have already exist. skip")
            else:
                try:
                    download_with_progressbar(url, tarpath)
                except Exception as e:
                    print("Error occurred when downloading file, error message:")
                    print(e)

            # unzip model tar
            try:
                with tarfile.open(tarpath, "r") as tarObj:
                    storage_dir = os.path.join(model_path, name)
                    os.makedirs(storage_dir, exist_ok=True)
                    for member in tarObj.getmembers():
                        filename = None
                        for tar_file_name in tar_file_name_list:
                            if tar_file_name in member.name:
                                filename = tar_file_name
                        if filename is None:
                            continue
                        file = tarObj.extractfile(member)
                        with open(os.path.join(storage_dir, filename), "wb") as f:
                            f.write(file.read())
            except Exception as e:
                print("Error occurred when unziping file, error message:")
                print(e)