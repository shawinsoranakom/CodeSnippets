async def _parse_classes(class_view_pathname: Path) -> List[DotClassInfo]:
        """
        Parses a dot format class view repository file.

        Args:
            class_view_pathname (Path): The path to the dot format class view repository file.

        Returns:
            List[DotClassInfo]: A list of DotClassInfo objects representing the parsed classes.
        """
        class_views = []
        if not class_view_pathname.exists():
            return class_views
        data = await aread(filename=class_view_pathname, encoding="utf-8")
        lines = data.split("\n")
        for line in lines:
            package_name, info = RepoParser._split_class_line(line)
            if not package_name:
                continue
            class_name, members, functions = re.split(r"(?<!\\)\|", info)
            class_info = DotClassInfo(name=class_name)
            class_info.package = package_name
            for m in members.split("\n"):
                if not m:
                    continue
                attr = DotClassAttribute.parse(m)
                class_info.attributes[attr.name] = attr
                for i in attr.compositions:
                    if i not in class_info.compositions:
                        class_info.compositions.append(i)
            for f in functions.split("\n"):
                if not f:
                    continue
                method = DotClassMethod.parse(f)
                class_info.methods[method.name] = method
                for i in method.aggregations:
                    if i not in class_info.compositions and i not in class_info.aggregations:
                        class_info.aggregations.append(i)
            class_views.append(class_info)
        return class_views