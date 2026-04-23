def format(self, record):
        metadata = copy.deepcopy(record.metadata)

        # Stub out values that are not stable across runs
        # TODO: Check that these match schema
        if "has_payload" in metadata:
            metadata["has_payload"] = "HASH"
        if "dynamo_start" in metadata:
            metadata["dynamo_start"]["stack"] = "STACK"
        if "inductor_output_code" in metadata:
            metadata["inductor_output_code"]["filename"] = "FILENAME"
            if "file_path" in metadata["inductor_output_code"]:
                metadata["inductor_output_code"]["file_path"] = "FILENAME"
        if "stack" in metadata:
            metadata["stack"] = "STACK"
        if "compilation_metrics" in metadata:
            metadata["compilation_metrics"] = "METRICS"
        if "bwd_compilation_metrics" in metadata:
            metadata["bwd_compilation_metrics"] = "METRICS"
        if "compilation_metrics_runtime" in metadata:
            metadata["compilation_metrics_runtime"] = "METRICS"
        if "bwd_compilation_metrics_runtime" in metadata:
            metadata["bwd_compilation_metrics_runtime"] = "METRICS"
        metadata = self._id_normalizer.normalize(metadata)
        if (
            (k := "create_symbol") in metadata
            or (k := "guard_added_fast") in metadata
            or (k := "create_unbacked_symbol") in metadata
        ):
            metadata[k]["user_stack"] = "STACK"
            metadata[k]["stack"] = "STACK"

        if "dump_file" in metadata:
            # Don't include the actually key number, that's sensitive to other
            # test runs
            metadata["dump_file"]["name"] = "<eval_with_key>"
            return (
                json.dumps(metadata)
                + "\n"
                + "\n".join(l.rstrip() for l in record.payload.splitlines())
            )

        return json.dumps(metadata)