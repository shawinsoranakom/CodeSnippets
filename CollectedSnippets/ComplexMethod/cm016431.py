def get_v1_info(self, cls) -> NodeInfoV1:
        # get V1 inputs
        input = create_input_dict_v1(self.inputs)
        if self.hidden:
            for hidden in self.hidden:
                input.setdefault("hidden", {})[hidden.name] = (hidden.value,)
        # create separate lists from output fields
        output = []
        output_is_list = []
        output_name = []
        output_tooltips = []
        output_matchtypes = []
        any_matchtypes = False
        if self.outputs:
            for o in self.outputs:
                output.append(o.io_type)
                output_is_list.append(o.is_output_list)
                output_name.append(o.display_name if o.display_name else o.io_type)
                output_tooltips.append(o.tooltip if o.tooltip else None)
                # special handling for MatchType
                if isinstance(o, MatchType.Output):
                    output_matchtypes.append(o.template.template_id)
                    any_matchtypes = True
                else:
                    output_matchtypes.append(None)

        # clear out lists that are all None
        if not any_matchtypes:
            output_matchtypes = None

        info = NodeInfoV1(
            input=input,
            input_order={key: list(value.keys()) for (key, value) in input.items()},
            is_input_list=self.is_input_list,
            output=output,
            output_is_list=output_is_list,
            output_name=output_name,
            output_tooltips=output_tooltips,
            output_matchtypes=output_matchtypes,
            name=self.node_id,
            display_name=self.display_name,
            category=self.category,
            description=self.description,
            output_node=self.is_output_node,
            has_intermediate_output=self.has_intermediate_output,
            deprecated=self.is_deprecated,
            experimental=self.is_experimental,
            dev_only=self.is_dev_only,
            api_node=self.is_api_node,
            python_module=getattr(cls, "RELATIVE_PYTHON_MODULE", "nodes"),
            price_badge=self.price_badge.as_dict(self.inputs) if self.price_badge is not None else None,
            search_aliases=self.search_aliases if self.search_aliases else None,
            essentials_category=self.essentials_category,
        )
        return info