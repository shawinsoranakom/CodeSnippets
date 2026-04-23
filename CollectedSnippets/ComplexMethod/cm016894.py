async def list_userdata_v2(request):
            """
            List files and directories in a user's data directory.

            This endpoint provides a structured listing of contents within a specified
            subdirectory of the user's data storage.

            Query Parameters:
            - path (optional): The relative path within the user's data directory
                               to list. Defaults to the root ('').

            Returns:
            - 400: If the requested path is invalid, outside the user's data directory, or is not a directory.
            - 404: If the requested path does not exist.
            - 403: If the user is invalid.
            - 500: If there is an error reading the directory contents.
            - 200: JSON response containing a list of file and directory objects.
                   Each object includes:
                   - name: The name of the file or directory.
                   - type: 'file' or 'directory'.
                   - path: The relative path from the user's data root.
                   - size (for files): The size in bytes.
                   - modified (for files): The last modified timestamp (Unix epoch).
            """
            requested_rel_path = request.rel_url.query.get('path', '')

            # URL-decode the path parameter
            try:
                requested_rel_path = parse.unquote(requested_rel_path)
            except Exception as e:
                logging.warning(f"Failed to decode path parameter: {requested_rel_path}, Error: {e}")
                return web.Response(status=400, text="Invalid characters in path parameter")


            # Check user validity and get the absolute path for the requested directory
            try:
                 base_user_path = self.get_request_user_filepath(request, None, create_dir=False)

                 if requested_rel_path:
                     target_abs_path = self.get_request_user_filepath(request, requested_rel_path, create_dir=False)
                 else:
                     target_abs_path = base_user_path

            except KeyError as e:
                 # Invalid user detected by get_request_user_id inside get_request_user_filepath
                 logging.warning(f"Access denied for user: {e}")
                 return web.Response(status=403, text="Invalid user specified in request")


            if not target_abs_path:
                 # Path traversal or other issue detected by get_request_user_filepath
                 return web.Response(status=400, text="Invalid path requested")

            # Handle cases where the user directory or target path doesn't exist
            if not os.path.exists(target_abs_path):
                # Check if it's the base user directory that's missing (new user case)
                if target_abs_path == base_user_path:
                    # It's okay if the base user directory doesn't exist yet, return empty list
                     return web.json_response([])
                else:
                    # A specific subdirectory was requested but doesn't exist
                     return web.Response(status=404, text="Requested path not found")

            if not os.path.isdir(target_abs_path):
                 return web.Response(status=400, text="Requested path is not a directory")

            results = []
            try:
                for root, dirs, files in os.walk(target_abs_path, topdown=True):
                    # Process directories
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        rel_path = os.path.relpath(dir_path, base_user_path).replace(os.sep, '/')
                        results.append({
                            "name": dir_name,
                            "path": rel_path,
                            "type": "directory"
                        })

                    # Process files
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        rel_path = os.path.relpath(file_path, base_user_path).replace(os.sep, '/')
                        entry_info = {
                            "name": file_name,
                            "path": rel_path,
                            "type": "file"
                        }
                        try:
                            stats = os.stat(file_path) # Use os.stat for potentially better performance with os.walk
                            entry_info["size"] = stats.st_size
                            entry_info["modified"] = stats.st_mtime
                        except OSError as stat_error:
                            logging.warning(f"Could not stat file {file_path}: {stat_error}")
                            pass # Include file with available info
                        results.append(entry_info)
            except OSError as e:
                logging.error(f"Error listing directory {target_abs_path}: {e}")
                return web.Response(status=500, text="Error reading directory contents")

            # Sort results alphabetically, directories first then files
            results.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))

            return web.json_response(results)