def _detect_processing_mode(cls):
        """Detect whether this node uses group or individual processing.

        Returns:
            bool: True if group processing, False if individual processing
        """
        # Explicit setting takes precedence
        if cls.is_group_process is not None:
            return cls.is_group_process

        # Check which method is overridden by looking at the defining class in MRO
        base_class = ImageProcessingNode

        # Find which class in MRO defines _process
        process_definer = None
        for klass in cls.__mro__:
            if "_process" in klass.__dict__:
                process_definer = klass
                break

        # Find which class in MRO defines _group_process
        group_definer = None
        for klass in cls.__mro__:
            if "_group_process" in klass.__dict__:
                group_definer = klass
                break

        # Check what was overridden (not defined in base class)
        has_process = process_definer is not None and process_definer is not base_class
        has_group = group_definer is not None and group_definer is not base_class

        if has_process and has_group:
            raise ValueError(
                f"{cls.__name__}: Cannot override both _process and _group_process. "
                "Override only one, or set is_group_process explicitly."
            )
        if not has_process and not has_group:
            raise ValueError(
                f"{cls.__name__}: Must override either _process or _group_process"
            )

        return has_group