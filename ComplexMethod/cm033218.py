def request(
            self,
            method: str,
            path: str,
            *,
            use_api_base: bool = True,
            auth_kind: Optional[str] = "api",
            headers: Optional[Dict[str, str]] = None,
            json_body: Optional[Dict[str, Any]] = None,
            data: Any = None,
            files: Any = None,
            params: Optional[Dict[str, Any]] = None,
            stream: bool = False,
            iterations: int = 1,
    ) -> requests.Response | dict:
        url = self.build_url(path, use_api_base=use_api_base)
        merged_headers = self._headers(auth_kind, headers)
        # timeout: Tuple[float, float] = (self.connect_timeout, self.read_timeout)
        session = requests.Session()
        # adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
        # session.mount("http://", adapter)
        http_function = typing.Any
        match method:
            case "GET":
                http_function = session.get
            case "POST":
                http_function = session.post
            case "PUT":
                http_function = session.put
            case "DELETE":
                http_function = session.delete
            case "PATCH":
                http_function = session.patch
            case _:
                raise ValueError(f"Invalid HTTP method: {method}")

        if iterations > 1:
            response_list = []
            total_duration = 0.0
            for _ in range(iterations):
                start_time = time.perf_counter()
                response = http_function(url, headers=merged_headers, json=json_body, data=data, stream=stream)
                # response = session.get(url, headers=merged_headers, json=json_body, data=data, stream=stream)
                # response = requests.request(
                #     method=method,
                #     url=url,
                #     headers=merged_headers,
                #     json=json_body,
                #     data=data,
                #     files=files,
                #     params=params,
                #     stream=stream,
                #     verify=self.verify_ssl,
                # )
                end_time = time.perf_counter()
                total_duration += end_time - start_time
                response_list.append(response)
            return {"duration": total_duration, "response_list": response_list}
        else:
            return http_function(url, headers=merged_headers, json=json_body, data=data, stream=stream)