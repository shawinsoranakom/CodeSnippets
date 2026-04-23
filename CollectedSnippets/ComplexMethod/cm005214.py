def from_dict(cls, config_dict: dict[str, Any], **kwargs):
        # Create a copy to avoid mutating the original dict
        config_dict = config_dict.copy()

        label_names = config_dict.get("label_names")
        is_custom_model = "num_labels" in kwargs or "id2label" in kwargs

        # if no labels added to config, use imagenet labeller in timm
        if label_names is None and not is_custom_model:
            requires_backends(cls, ["timm"])
            imagenet_subset = infer_imagenet_subset(config_dict)
            if imagenet_subset:
                dataset_info = ImageNetInfo(imagenet_subset)
                synsets = dataset_info.label_names()
                label_descriptions = dataset_info.label_descriptions(as_dict=True)
                label_names = [label_descriptions[synset] for synset in synsets]

        if label_names is not None and not is_custom_model:
            kwargs["id2label"] = dict(enumerate(label_names))

            # if all label names are unique, create label2id mapping as well
            if len(set(label_names)) == len(label_names):
                kwargs["label2id"] = {name: i for i, name in enumerate(label_names)}
            else:
                kwargs["label2id"] = None

        # timm config stores the `num_classes` attribute in both the root of config and in the "pretrained_cfg" dict.
        # We are removing these attributes in order to have the native `transformers` num_labels attribute in config
        # and to avoid duplicate attributes
        num_labels_in_kwargs = kwargs.pop("num_labels", None)
        num_labels_in_dict = config_dict.pop("num_classes", None)

        # passed num_labels has priority over num_classes in config_dict
        kwargs["num_labels"] = num_labels_in_kwargs or num_labels_in_dict

        # pop num_classes from "pretrained_cfg",
        # it is not necessary to have it, only root one is used in timm
        if "pretrained_cfg" in config_dict and "num_classes" in config_dict["pretrained_cfg"]:
            config_dict["pretrained_cfg"].pop("num_classes", None)

        return super().from_dict(config_dict, **kwargs)