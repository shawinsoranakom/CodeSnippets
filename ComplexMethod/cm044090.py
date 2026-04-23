def serialize_model(self) -> dict:
        """Serialize statsmodels objects to a dictionary."""
        results = self.results
        conf_int = results.conf_int()
        conf_int_dict = (
            conf_int.to_dict()
            if hasattr(conf_int, "to_dict")
            else conf_int.to_dict("index")
        )
        return {
            "params": (
                results.params.to_dict()
                if hasattr(results.params, "to_dict")
                else dict(results.params)
            ),
            "rsquared": float(results.rsquared),
            "rsquared_adj": float(results.rsquared_adj),
            "fvalue": float(results.fvalue) if results.fvalue is not None else None,
            "f_pvalue": (
                float(results.f_pvalue) if results.f_pvalue is not None else None
            ),
            "aic": float(results.aic),
            "bic": float(results.bic),
            "llf": float(results.llf),
            "nobs": int(results.nobs),
            "df_model": float(results.df_model),
            "df_resid": float(results.df_resid),
            "pvalues": (
                results.pvalues.to_dict()
                if hasattr(results.pvalues, "to_dict")
                else dict(results.pvalues)
            ),
            "tvalues": (
                results.tvalues.to_dict()
                if hasattr(results.tvalues, "to_dict")
                else dict(results.tvalues)
            ),
            "bse": (
                results.bse.to_dict()
                if hasattr(results.bse, "to_dict")
                else dict(results.bse)
            ),
            "conf_int": conf_int_dict,
        }