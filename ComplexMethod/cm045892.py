def _resolve_run_bool_with_inheritance(
        cls,
        run: Run,
        attr_name: str,
    ) -> bool:
        """解析 run 的字体属性，支持 run/字符样式/段落样式继承。"""
        if attr_name == "underline":
            direct_value = run.underline
        elif attr_name == "strikethrough":
            direct_value = run.font.strike
        else:
            direct_value = getattr(run, attr_name, None)

        if direct_value is not None:
            return bool(direct_value)

        # 先看 run 级字符样式链（跳过 Hyperlink 默认字符样式，避免把默认下划线
        # 误当作正文强调样式注入到解析结果中）
        run_style = getattr(run, "style", None)
        run_style_id = str(getattr(run_style, "style_id", "") or "").lower()
        run_style_name = str(getattr(run_style, "name", "") or "").lower()
        is_hyperlink_style = (
            run_style_id == "hyperlink" or "hyperlink" in run_style_name
        )
        if not is_hyperlink_style:
            inherited = cls._resolve_style_chain_bool(run_style, attr_name)
            if inherited is not None:
                return inherited

        # 再看所在段落样式链
        parent = getattr(run, "_parent", None)
        inherited = cls._resolve_style_chain_bool(getattr(parent, "style", None), attr_name)
        if inherited is not None:
            return inherited

        return False