def list_certificates(
        self,
        context: RequestContext,
        request: ListCertificatesRequest,
    ) -> ListCertificatesResponse:
        response = moto.call_moto(context)
        summaries = response.get("CertificateSummaryList") or []
        for summary in summaries:
            if "KeyUsages" in summary:
                summary["KeyUsages"] = [
                    k["Name"] if isinstance(k, dict) else k for k in summary["KeyUsages"]
                ]
            if "ExtendedKeyUsages" in summary:
                summary["ExtendedKeyUsages"] = [
                    k["Name"] if isinstance(k, dict) else k for k in summary["ExtendedKeyUsages"]
                ]
        return response