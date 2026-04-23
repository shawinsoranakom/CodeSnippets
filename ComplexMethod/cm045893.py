def _get_format_from_run(cls, run: Run) -> Optional[Formatting]:
        """
        从 Run 对象获取格式信息。

        Args:
            run: Run 对象

        Returns:
            Optional[Formatting]: 格式对象
        """
        is_bold = cls._resolve_run_bool_with_inheritance(run, "bold")
        is_italic = cls._resolve_run_bool_with_inheritance(run, "italic")
        is_strikethrough = cls._resolve_run_bool_with_inheritance(run, "strikethrough")
        is_underline = cls._resolve_run_bool_with_inheritance(run, "underline")

        # 检测着重符号 (w:em)：若存在非 none 的 em 值，则视为下划线样式
        _W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        rPr = run._element.find(f'{{{_W}}}rPr')
        if rPr is not None:
            em = rPr.find(f'{{{_W}}}em')
            if em is not None:
                em_val = em.get(f'{{{_W}}}val', '')
                if em_val and em_val != 'none':
                    is_underline = True

        is_sub = run.font.subscript or False
        is_sup = run.font.superscript or False
        script = Script.SUB if is_sub else Script.SUPER if is_sup else Script.BASELINE

        return Formatting(
            bold=is_bold,
            italic=is_italic,
            underline=is_underline,
            strikethrough=is_strikethrough,
            script=script,
        )