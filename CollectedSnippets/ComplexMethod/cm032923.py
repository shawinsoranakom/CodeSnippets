def __open__(self):
        try:
            if self.conn:
                self.__close__()
        except Exception:
            pass

        try:
            s3_params = {}
            config_kwargs = {}
            # if not set ak/sk, boto3 s3 client would try several ways to do the authentication
            # see doc: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials
            if self.access_key and self.secret_key:
                s3_params = {
                    'aws_access_key_id': self.access_key,
                    'aws_secret_access_key': self.secret_key,
                    'aws_session_token': self.session_token,
                }
            if self.region_name:
                s3_params['region_name'] = self.region_name
            if self.endpoint_url:
                s3_params['endpoint_url'] = self.endpoint_url

            # Configure signature_version and addressing_style through Config object
            if self.signature_version:
                config_kwargs['signature_version'] = self.signature_version
            if self.addressing_style:
                config_kwargs['s3'] = {'addressing_style': self.addressing_style}

            if config_kwargs:
                s3_params['config'] = Config(**config_kwargs)

            self.conn = [boto3.client('s3', **s3_params)]
        except Exception:
            logging.exception(f"Fail to connect at region {self.region_name} or endpoint {self.endpoint_url}")