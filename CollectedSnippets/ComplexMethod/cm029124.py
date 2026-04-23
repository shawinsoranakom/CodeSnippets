def calculate_paint_order(self) -> None:
		all_simplified_nodes_with_paint_order: list[SimplifiedNode] = []

		def collect_paint_order(node: SimplifiedNode) -> None:
			if (
				node.original_node.snapshot_node
				and node.original_node.snapshot_node.paint_order is not None
				and node.original_node.snapshot_node.bounds is not None
			):
				all_simplified_nodes_with_paint_order.append(node)

			for child in node.children:
				collect_paint_order(child)

		collect_paint_order(self.root)

		grouped_by_paint_order: defaultdict[int, list[SimplifiedNode]] = defaultdict(list)

		for node in all_simplified_nodes_with_paint_order:
			if node.original_node.snapshot_node and node.original_node.snapshot_node.paint_order is not None:
				grouped_by_paint_order[node.original_node.snapshot_node.paint_order].append(node)

		rect_union = RectUnionPure()

		for paint_order, nodes in sorted(grouped_by_paint_order.items(), key=lambda x: -x[0]):
			rects_to_add = []

			for node in nodes:
				if not node.original_node.snapshot_node or not node.original_node.snapshot_node.bounds:
					continue  # shouldn't happen by how we filter them out in the first place

				rect = Rect(
					x1=node.original_node.snapshot_node.bounds.x,
					y1=node.original_node.snapshot_node.bounds.y,
					x2=node.original_node.snapshot_node.bounds.x + node.original_node.snapshot_node.bounds.width,
					y2=node.original_node.snapshot_node.bounds.y + node.original_node.snapshot_node.bounds.height,
				)

				if rect_union.contains(rect):
					node.ignored_by_paint_order = True

				# don't add to the nodes if opacity is less then 0.95 or background-color is transparent
				if (
					node.original_node.snapshot_node.computed_styles
					and node.original_node.snapshot_node.computed_styles.get('background-color', 'rgba(0, 0, 0, 0)')
					== 'rgba(0, 0, 0, 0)'
				) or (
					node.original_node.snapshot_node.computed_styles
					and float(node.original_node.snapshot_node.computed_styles.get('opacity', '1'))
					< 0.8  # this is highly vibes based number
				):
					continue

				rects_to_add.append(rect)

			for rect in rects_to_add:
				rect_union.add(rect)

		return None