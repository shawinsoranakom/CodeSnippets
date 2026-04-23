def parse_metadata(self, model_name, repo_path=DEFAULT_MODEL_DIR, method="best"):
        p = Path(repo_path) / model_name

        def url_to_name(url):
            return url.split("/")[-1].split(".")[0]

        if model_name not in self.model_results:
            # This is not a language pair, so model results are ambiguous, go by newest
            method = "newest"

        if method == "best":
            # Sort by how early they appear in released-models-results
            results = [url_to_name(model["download"]) for model in self.model_results[model_name]]
            ymls = [f for f in os.listdir(p) if f.endswith(".yml") and f[:-4] in results]
            ymls.sort(key=lambda x: results.index(x[:-4]))
            metadata = yaml.safe_load(open(p / ymls[0]))
            metadata.update(self.model_type_info_from_model_name(ymls[0][:-4]))
        elif method == "newest":
            ymls = [f for f in os.listdir(p) if f.endswith(".yml")]
            # Sort by date
            ymls.sort(
                key=lambda x: datetime.datetime.strptime(re.search(r"\d\d\d\d-\d\d?-\d\d?", x).group(), "%Y-%m-%d")
            )
            metadata = yaml.safe_load(open(p / ymls[-1]))
            metadata.update(self.model_type_info_from_model_name(ymls[-1][:-4]))
        else:
            raise NotImplementedError(f"Don't know argument method='{method}' to parse_metadata()")
        metadata["_name"] = model_name
        return metadata