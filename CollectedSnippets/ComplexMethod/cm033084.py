def reconstruct_document_sse(self, file_type, file_url=None, file_base64=None, file_start_page=1, file_end_page=1000, config=None):
        """Call document parsing API using official SDK"""
        try:
            # Instantiate a request object, each interface corresponds to a request object
            req = models.ReconstructDocumentSSERequest()

            # Build request parameters
            params = {
                "FileType": file_type,
                "FileStartPageNumber": file_start_page,
                "FileEndPageNumber": file_end_page,
            }

            # According to Tencent Cloud API documentation, either FileUrl or FileBase64 parameter must be provided, if both are provided only FileUrl will be used
            if file_url:
                params["FileUrl"] = file_url
                logging.info(f"[TCADP] Using file URL: {file_url}")
            elif file_base64:
                params["FileBase64"] = file_base64
                logging.info(f"[TCADP] Using Base64 data, length: {len(file_base64)} characters")
            else:
                raise ValueError("Must provide either FileUrl or FileBase64 parameter")

            if config:
                params["Config"] = config

            req.from_json_string(json.dumps(params))

            # The returned resp is an instance of ReconstructDocumentSSEResponse, corresponding to the request object
            resp = self.client.ReconstructDocumentSSE(req)
            parser_result = {}

            # Output json format string response
            if isinstance(resp, types.GeneratorType):  # Streaming response
                logging.info("[TCADP] Detected streaming response")
                for event in resp:
                    logging.info(f"[TCADP] Received event: {event}")
                    if event.get('data'):
                        try:
                            data_dict = json.loads(event['data'])
                            logging.info(f"[TCADP] Parsed data: {data_dict}")

                            if data_dict.get('Progress') == "100":
                                parser_result = data_dict
                                logging.info("[TCADP] Document parsing completed!")
                                logging.info(f"[TCADP] Task ID: {data_dict.get('TaskId')}")
                                logging.info(f"[TCADP] Success pages: {data_dict.get('SuccessPageNum')}")
                                logging.info(f"[TCADP] Failed pages: {data_dict.get('FailPageNum')}")

                                # Print failed page information
                                failed_pages = data_dict.get("FailedPages", [])
                                if failed_pages:
                                    logging.warning("[TCADP] Failed parsing pages:")
                                    for page in failed_pages:
                                        logging.warning(f"[TCADP]   Page number: {page.get('PageNumber')}, Error: {page.get('ErrorMsg')}")

                                # Check if there is a download link
                                download_url = data_dict.get("DocumentRecognizeResultUrl")
                                if download_url:
                                    logging.info(f"[TCADP] Got download link: {download_url}")
                                else:
                                    logging.warning("[TCADP] No download link obtained")

                                break  # Found final result, exit loop
                            else:
                                # Print progress information
                                progress = data_dict.get("Progress", "0")
                                logging.info(f"[TCADP] Progress: {progress}%")
                        except json.JSONDecodeError as e:
                            logging.error(f"[TCADP] Failed to parse JSON data: {e}")
                            logging.error(f"[TCADP] Raw data: {event.get('data')}")
                            continue
                    else:
                        logging.info(f"[TCADP] Event without data: {event}")
            else:  # Non-streaming response
                logging.info("[TCADP] Detected non-streaming response")
                if hasattr(resp, 'data') and resp.data:
                    try:
                        data_dict = json.loads(resp.data)
                        parser_result = data_dict
                        logging.info(f"[TCADP] JSON parsing successful: {parser_result}")
                    except json.JSONDecodeError as e:
                        logging.error(f"[TCADP] JSON parsing failed: {e}")
                        return None
                else:
                    logging.error("[TCADP] No data in response")
                    return None

            return parser_result

        except TencentCloudSDKException as err:
            logging.error(f"[TCADP] Tencent Cloud SDK error: {err}")
            return None
        except Exception as e:
            logging.error(f"[TCADP] Unknown error: {e}")
            logging.error(f"[TCADP] Error stack trace: {traceback.format_exc()}")
            return None