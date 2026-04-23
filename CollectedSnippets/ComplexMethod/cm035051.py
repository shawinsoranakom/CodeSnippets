def build(self, args, root=True):
        if args is None or len(args) == 0:
            return None
        elif isinstance(args, list):
            # Build the full augmentation sequence if it's a root-level call
            if root:
                sequence = [self.build(value, root=False) for value in args]
                return A.Compose(
                    sequence,
                    keypoint_params=A.KeypointParams(
                        format="xy", remove_invisible=False
                    ),
                )
            else:
                # Build individual augmenters for nested arguments
                augmenter_type = args[0]
                augmenter_args = args[1] if len(args) > 1 else {}
                augmenter_args_mapped = self.map_arguments(
                    augmenter_type, augmenter_args
                )
                augmenter_type_mapped = self.imgaug_to_albu.get(
                    augmenter_type, augmenter_type
                )
                if augmenter_type_mapped == "Resize":
                    return ImgaugLikeResize(**augmenter_args_mapped)
                else:
                    cls = getattr(A, augmenter_type_mapped)
                    return cls(
                        **{
                            k: self.to_tuple_if_list(v)
                            for k, v in augmenter_args_mapped.items()
                        }
                    )
        elif isinstance(args, dict):
            # Process individual transformation specified as dictionary
            augmenter_type = args["type"]
            augmenter_args = args.get("args", {})
            augmenter_args_mapped = self.map_arguments(augmenter_type, augmenter_args)
            augmenter_type_mapped = self.imgaug_to_albu.get(
                augmenter_type, augmenter_type
            )
            if augmenter_type_mapped == "Resize":
                return ImgaugLikeResize(**augmenter_args_mapped)
            else:
                cls = getattr(A, augmenter_type_mapped)
                return cls(
                    **{
                        k: self.to_tuple_if_list(v)
                        for k, v in augmenter_args_mapped.items()
                    }
                )
        else:
            raise RuntimeError("Unknown augmenter arg: " + str(args))