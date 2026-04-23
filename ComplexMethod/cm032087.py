def convert_to_pdf(word_path: Union[str, Path], pdf_path: Union[str, Path] = None) -> str:
        """
        将Word文档转换为PDF

        参数:
            word_path: Word文档的路径
            pdf_path: 可选，PDF文件的输出路径。如果未指定，将使用与Word文档相同的名称和位置

        返回:
            生成的PDF文件路径

        异常:
            如果转换失败，将抛出相应异常
        """
        try:
            # 确保输入路径是Path对象
            word_path = Path(word_path)

            # 如果未指定pdf_path，则使用与word文档相同的名称
            if pdf_path is None:
                pdf_path = word_path.with_suffix('.pdf')
            else:
                pdf_path = Path(pdf_path)

            # 检查操作系统
            if platform.system() == 'Linux':
                # Linux系统需要安装libreoffice
                which_result = subprocess.run(['which', 'libreoffice'], capture_output=True, text=True)
                if which_result.returncode != 0:
                    raise RuntimeError("请先安装LibreOffice: sudo apt-get install libreoffice")

                print(f"开始转换Word文档: {word_path} 到 PDF")

                # 使用subprocess代替os.system
                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'pdf:writer_pdf_Export',
                     str(word_path), '--outdir', str(pdf_path.parent)],
                    capture_output=True, text=True
                )

                if result.returncode != 0:
                    error_msg = result.stderr or "未知错误"
                    print(f"LibreOffice转换失败，错误信息: {error_msg}")
                    raise RuntimeError(f"LibreOffice转换失败: {error_msg}")

                print(f"LibreOffice转换输出: {result.stdout}")

                # 如果输出路径与默认生成的不同，则重命名
                default_pdf = word_path.with_suffix('.pdf')
                if default_pdf != pdf_path and default_pdf.exists():
                    os.rename(default_pdf, pdf_path)
                    print(f"已将PDF从 {default_pdf} 重命名为 {pdf_path}")

                # 验证PDF是否成功生成
                if not pdf_path.exists() or pdf_path.stat().st_size == 0:
                    raise RuntimeError("PDF生成失败或文件为空")

                print(f"PDF转换成功，文件大小: {pdf_path.stat().st_size} 字节")
            else:
                # Windows和MacOS使用docx2pdf
                print(f"使用docx2pdf转换 {word_path} 到 {pdf_path}")
                convert(word_path, pdf_path)

                # 验证PDF是否成功生成
                if not pdf_path.exists() or pdf_path.stat().st_size == 0:
                    raise RuntimeError("PDF生成失败或文件为空")

                print(f"PDF转换成功，文件大小: {pdf_path.stat().st_size} 字节")

            return str(pdf_path)

        except Exception as e:
            print(f"PDF转换异常: {str(e)}")
            raise Exception(f"转换PDF失败: {str(e)}")