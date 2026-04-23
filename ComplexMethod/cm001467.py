def load_model(self, path: str):
        # Remove incorrect project.yaml file if too big
        yaml_path = os.path.join(self.model_path, "project.yaml")
        old_model_path = os.path.join(self.model_path, "model.pth")
        new_model_path = os.path.join(self.model_path, "model.ckpt")

        local_model_paths = self.find_models(ext_filter=[".ckpt", ".safetensors"])
        local_ckpt_path = next(iter([local_model for local_model in local_model_paths if local_model.endswith("model.ckpt")]), None)
        local_safetensors_path = next(iter([local_model for local_model in local_model_paths if local_model.endswith("model.safetensors")]), None)
        local_yaml_path = next(iter([local_model for local_model in local_model_paths if local_model.endswith("project.yaml")]), None)

        if os.path.exists(yaml_path):
            statinfo = os.stat(yaml_path)
            if statinfo.st_size >= 10485760:
                print("Removing invalid LDSR YAML file.")
                os.remove(yaml_path)

        if os.path.exists(old_model_path):
            print("Renaming model from model.pth to model.ckpt")
            os.rename(old_model_path, new_model_path)

        if local_safetensors_path is not None and os.path.exists(local_safetensors_path):
            model = local_safetensors_path
        else:
            model = local_ckpt_path or load_file_from_url(self.model_url, model_dir=self.model_download_path, file_name="model.ckpt")

        yaml = local_yaml_path or load_file_from_url(self.yaml_url, model_dir=self.model_download_path, file_name="project.yaml")

        return LDSR(model, yaml)