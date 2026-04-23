async def run(
        self,
        input_data: Input,
        *,
        credentials: TodoistCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            label_args = {}
            if input_data.name is not None:
                label_args["name"] = input_data.name
            if input_data.order is not None:
                label_args["order"] = input_data.order
            if input_data.color is not None:
                label_args["color"] = input_data.color.value
            if input_data.is_favorite is not None:
                label_args["is_favorite"] = input_data.is_favorite

            success = self.update_label(
                credentials,
                input_data.label_id,
                **{k: v for k, v in label_args.items() if v is not None},
            )

            yield "success", success

        except Exception as e:
            yield "error", str(e)