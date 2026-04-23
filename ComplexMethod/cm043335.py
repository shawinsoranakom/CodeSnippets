def render_tag(elem):
            if not isinstance(elem, Tag):
                if isinstance(elem, str):
                    builder.append(elem.strip())
                return

            if elem.name in unwanted_tags:
                return

            # Start tag
            builder.append(f"<{elem.name}")

            # Add cleaned attributes
            attrs = {k: v for k, v in elem.attrs.items() if k not in unwanted_attrs}
            for key, value in attrs.items():
                builder.append(f' {key}="{value}"')

            builder.append(">")

            # Process children
            for child in elem.children:
                render_tag(child)

            # Close tag
            builder.append(f"</{elem.name}>")