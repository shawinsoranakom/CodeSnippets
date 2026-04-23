def _resolve_refpath(self, refpath: str) -> dict:
        if refpath in self._refpaths and not self.allow_recursive:
            raise Exception("recursion detected with allow_recursive=False")

        # We don't resolve the Model definition, we will return a absolute reference to the model like AWS
        # When validating the schema, we will need to resolve the $ref there
        # Because if we resolved all $ref in schema, it can lead to circular references in complex schemas
        if self.current_path.startswith("#/definitions") or self.current_path.startswith(
            "#/components/schemas"
        ):
            return {"$ref": f"{self._base_url}{refpath.rsplit('/', maxsplit=1)[-1]}"}

        # We should not resolve the Model either, because we need its name to set it to the Request/ResponseModels,
        # it just makes our job more difficult to retrieve the Model name
        # We still need to verify that the ref exists
        is_schema = self.current_path.endswith("schema")

        if refpath in self._cache and not is_schema:
            return self._cache.get(refpath)

        with self._pathctx(refpath):
            if self._is_internal_ref(self.current_path):
                cur = self.document
            else:
                raise NotImplementedError("External references not yet supported.")

            for step in self.current_path.split("/")[1:]:
                cur = cur.get(step)

            self._cache[self.current_path] = cur

            if is_schema:
                # If the $ref doesn't exist in our schema, return None, otherwise return the ref
                return {"$ref": refpath} if cur else None

            return cur