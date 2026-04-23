def __call__(
        self,
        images: ImageInput | None = None,
        text=None,
        **kwargs: Unpack[ShieldGemma2ProcessorKwargs],
    ) -> BatchFeature:
        """Generates a batch of inputs from the provided images.

        ShieldGemma was trained to classify image content for policy compliance using a specific prompt construction.
        This processor generates a batch of such prompts from the provided images by:

        1.  Creating a list of conversations, one for each `<image, policy>` pair;
        2.  Converting these conversations to text using `self.apply_chat_template()`; and
        3.  Encoding the conversations and images using the same techniques as `Gemma3Processor`.

        Args:
            images: A single image or a list of images to include in the batch.
            text: Not supported.
            videos: Not supported.
            audio: Not supported.
            kwargs: An optional dictionary of keyword arguments to configure the
                processor. Possible values include:

                *   `custom_policies`: Additional policy definitions that augment the `self.policy_definitions` passed
                    into the constructor. Note that `custom_policies` that share a key with `self.policy_definitions`
                    will override the policy description
                *   `policies`: (Optional) a list of keys in the joint `self.policy_definitions | custom_policies`
                    dictionary of specific interest for the provided images. If empty or None, prompts will be
                    generated for every key in the joint dictionary.

        Returns:
            A `BatchFeature` containing `input_ids`, `pixel_values`, etc. where each Tensor is of shape
            `(len(images) * len(policies), )`, and the order within the batch will be
            img1_policy1, ... img1_policyN, ... imgM_policyN.
        """
        if not images:
            raise ValueError("ShieldGemma 2 needs images to classify")
        elif not isinstance(images, Sequence):
            images = [images]

        if not self.chat_template:
            raise ValueError("ShieldGemma 2 requires the use of a specific chat template")

        common_kwargs = kwargs.setdefault("common_kwargs", {})
        if "return_tensors" in kwargs:
            common_kwargs["return_tensors"] = kwargs.pop("return_tensors")

        # Disable pan and scan
        images_kwargs = kwargs.setdefault("images_kwargs", {})
        if images_kwargs.get("do_pan_and_scan") is True:
            logger.warning_once("ShieldGemma2 does not support pan and scan.")
            images_kwargs["do_pan_and_scan"] = False

        # Enable padding on the batch during tokenization
        text_kwargs = kwargs.setdefault("text_kwargs", {})
        if "padding" not in text_kwargs:
            text_kwargs["padding"] = kwargs.pop("padding", True)
            text_kwargs["padding_side"] = kwargs.pop("padding_side", "left")

        policy_definitions: Mapping[str, str] = {
            **self.policy_definitions,
            **kwargs.get("custom_policies", {}),
        }

        if (policies := kwargs.get("policies")) is None:
            policies = list(policy_definitions.keys())

        # TODO(ryanmullins): Support images from PIL or URLs.
        messages = []
        expanded_images = []
        for img in images:
            if not isinstance(img, list):
                img = [img]
            elif len(img) > 1:
                raise ValueError(f"SheildGemma can process at most one image per sample, but got {len(img)} images")

            for policy in policies:
                if img:
                    messages.append(
                        [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image"},
                                    {"type": "text", "text": policy_definitions[policy]},
                                ],
                            }
                        ]
                    )
                else:
                    messages.append(
                        [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": policy_definitions[policy]},
                                ],
                            }
                        ]
                    )
                expanded_images.append(img)

        text = self.apply_chat_template(messages, tokenize=False)
        return super().__call__(images=expanded_images, text=text, **kwargs)