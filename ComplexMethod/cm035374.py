def delete(self, path: str) -> None:
        try:
            # Sanitize path
            if not path or path == '/':
                path = ''
            if path.endswith('/'):
                path = path[:-1]

            # Try to delete any child resources (Assume the path is a directory)
            response = self.client.list_objects_v2(
                Bucket=self.bucket, Prefix=f'{path}/'
            )
            for content in response.get('Contents') or []:
                self.client.delete_object(Bucket=self.bucket, Key=content['Key'])

            # Next try to delete item as a file
            self.client.delete_object(Bucket=self.bucket, Key=path)

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                raise FileNotFoundError(
                    f"Error: The bucket '{self.bucket}' does not exist."
                )
            elif e.response['Error']['Code'] == 'AccessDenied':
                raise FileNotFoundError(
                    f"Error: Access denied to bucket '{self.bucket}'."
                )
            elif e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(
                    f"Error: The object key '{path}' does not exist in bucket '{self.bucket}'."
                )
            else:
                raise FileNotFoundError(
                    f"Error: Failed to delete key '{path}' from bucket '{self.bucket}': {e}"
                )
        except Exception as e:
            raise FileNotFoundError(
                f"Error: Failed to delete key '{path}' from bucket '{self.bucket}: {e}"
            )