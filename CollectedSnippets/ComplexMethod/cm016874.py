def execute(cls, mesh: Types.MESH | Types.File3D, filename_prefix: str) -> IO.NodeOutput:
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, folder_paths.get_output_directory())
        results = []

        metadata = {}
        if not args.disable_metadata:
            if cls.hidden.prompt is not None:
                metadata["prompt"] = json.dumps(cls.hidden.prompt)
            if cls.hidden.extra_pnginfo is not None:
                for x in cls.hidden.extra_pnginfo:
                    metadata[x] = json.dumps(cls.hidden.extra_pnginfo[x])

        if isinstance(mesh, Types.File3D):
            # Handle File3D input - save BytesIO data to output folder
            ext = mesh.format or "glb"
            f = f"{filename}_{counter:05}_.{ext}"
            mesh.save_to(os.path.join(full_output_folder, f))
            results.append({
                "filename": f,
                "subfolder": subfolder,
                "type": "output"
            })
        else:
            # Handle Mesh input - save vertices and faces as GLB
            for i in range(mesh.vertices.shape[0]):
                f = f"{filename}_{counter:05}_.glb"
                save_glb(mesh.vertices[i], mesh.faces[i], os.path.join(full_output_folder, f), metadata)
                results.append({
                    "filename": f,
                    "subfolder": subfolder,
                    "type": "output"
                })
                counter += 1
        return IO.NodeOutput(ui={"3d": results})