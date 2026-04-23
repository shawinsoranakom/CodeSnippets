def previousIndex(self, attrs: Dict[str, Optional[str]]) -> Optional[int]:
        """
        :type attrs: dict

        :returns: The index of certain set of attributes (of a link) in the
        self.a list. If the set of attributes is not found, returns None
        :rtype: int
        """
        if "href" not in attrs:
            return None

        match = False
        for i, a in enumerate(self.a):
            if "href" in a.attrs and a.attrs["href"] == attrs["href"]:
                if "title" in a.attrs or "title" in attrs:
                    if (
                        "title" in a.attrs
                        and "title" in attrs
                        and a.attrs["title"] == attrs["title"]
                    ):
                        match = True
                else:
                    match = True

            if match:
                return i
        return None