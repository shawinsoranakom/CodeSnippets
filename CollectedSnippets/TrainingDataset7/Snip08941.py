async def aget_object_list(self):
        """
        Returns self.object_list as a list.

        This method must be awaited before AsyncPage can be
        treated as a sequence of self.object_list.
        """
        if not isinstance(self.object_list, list):
            if hasattr(self.object_list, "__aiter__"):
                self.object_list = [obj async for obj in self.object_list]
            else:
                self.object_list = await sync_to_async(list)(self.object_list)
        return self.object_list