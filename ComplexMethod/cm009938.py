def to_dataframe(self) -> pd.DataFrame:
        """Convert the results to a dataframe."""
        try:
            import pandas as pd
        except ImportError as e:
            msg = (
                "Pandas is required to convert the results to a dataframe."
                " to install pandas, run `pip install pandas`."
            )
            raise ImportError(msg) from e

        indices = []
        records = []
        for example_id, result in self["results"].items():
            feedback = result["feedback"]
            output_ = result.get("output")
            if isinstance(output_, dict):
                output = {f"outputs.{k}": v for k, v in output_.items()}
            elif output_ is None:
                output = {}
            else:
                output = {"output": output_}

            r = {
                **{f"inputs.{k}": v for k, v in result["input"].items()},
                **output,
            }
            if "reference" in result:
                if isinstance(result["reference"], dict):
                    r.update(
                        {f"reference.{k}": v for k, v in result["reference"].items()},
                    )
                else:
                    r["reference"] = result["reference"]
            r.update(
                {
                    **{f"feedback.{f.key}": f.score for f in feedback},
                    "error": result.get("Error"),
                    "execution_time": result["execution_time"],
                    "run_id": result.get("run_id"),
                },
            )
            records.append(r)
            indices.append(example_id)

        return pd.DataFrame(records, index=indices)