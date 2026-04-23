def main():
    """主函数：演示用法"""
    # 创建提取器
    extractor = PaperStructureExtractor()

    # 使用示例
    try:
        # 替换为实际的文件路径
        sample_file = '/Users/boyin.liu/Documents/示例文档/论文/3.pdf'
        if Path(sample_file).exists():
            paper = extractor.extract_paper_structure(sample_file)

            print("\n===== 论文结构化信息 =====")
            print(f"标题: {paper.metadata.title}")
            print(f"作者: {', '.join(paper.metadata.authors)}")

            print("\n--- 章节结构 ---")
            for i, section in enumerate(paper.sections):
                print(f"{i+1}. {section.title} ({section.section_type})")
                if section.subsections:
                    for j, subsection in enumerate(section.subsections):
                        print(f"   {i+1}.{j+1} {subsection.title}")

            print("\n--- 图表 ---")
            print(f"图: {len(paper.figures)}")
            for i, fig in enumerate(paper.figures[:3]):
                print(f"图 {i+1}: {fig.caption[:50]}...")

            print(f"\n表: {len(paper.tables)}")
            for i, table in enumerate(paper.tables[:3]):
                print(f"表 {i+1}: {table.caption[:50]}...")

            print(f"\n--- 公式: {len(paper.formulas)} ---")
            for i, formula in enumerate(paper.formulas[:3]):
                print(f"公式 {formula.id}: {formula.content[:30]}...")

            print(f"\n--- 参考文献: {len(paper.references)} ---")
            for i, ref in enumerate(paper.references[:5]):
                print(f"{ref.id} {ref.text[:50]}...")

            print("\n--- 摘要 ---")
            abstract_section = next((s for s in paper.sections if s.section_type == 'abstract'), None)
            if abstract_section:
                print(abstract_section.content[:200] + "...")
            else:
                print(paper.metadata.abstract[:200] + "...")

        else:
            print(f"示例文件 {sample_file} 不存在")

        print("\n支持的格式:", extractor.get_supported_formats())

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()