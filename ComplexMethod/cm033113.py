def _assign_column(self, boxes, zoomin=3):
        if not boxes:
            return boxes
        if all("col_id" in b for b in boxes):
            return boxes

        by_page = defaultdict(list)
        for b in boxes:
            by_page[b["page_number"]].append(b)

        page_cols = {}

        for pg, bxs in by_page.items():
            if not bxs:
                page_cols[pg] = 1
                continue

            x0s_raw = np.array([b["x0"] for b in bxs], dtype=float)

            min_x0 = np.min(x0s_raw)
            max_x1 = np.max([b["x1"] for b in bxs])
            width = max_x1 - min_x0

            INDENT_TOL = width * 0.12
            x0s = []
            for x in x0s_raw:
                if abs(x - min_x0) < INDENT_TOL:
                    x0s.append([min_x0])
                else:
                    x0s.append([x])
            x0s = np.array(x0s, dtype=float)

            max_try = min(4, len(bxs))
            if max_try < 2:
                max_try = 1
            best_k = 1
            best_score = -1

            for k in range(1, max_try + 1):
                km = KMeans(n_clusters=k, n_init="auto")
                labels = km.fit_predict(x0s)

                centers = np.sort(km.cluster_centers_.flatten())
                if len(centers) > 1:
                    try:
                        score = silhouette_score(x0s, labels)
                    except ValueError:
                        continue
                else:
                    score = 0
                if score > best_score:
                    best_score = score
                    best_k = k

            page_cols[pg] = best_k
            logging.info(f"[Page {pg}] best_score={best_score:.2f}, best_k={best_k}")

        global_cols = Counter(page_cols.values()).most_common(1)[0][0]
        logging.info(f"Global column_num decided by majority: {global_cols}")

        for pg, bxs in by_page.items():
            if not bxs:
                continue
            k = page_cols[pg]
            if len(bxs) < k:
                k = 1
            x0s = np.array([[b["x0"]] for b in bxs], dtype=float)
            km = KMeans(n_clusters=k, n_init="auto")
            labels = km.fit_predict(x0s)

            centers = km.cluster_centers_.flatten()
            order = np.argsort(centers)

            remap = {orig: new for new, orig in enumerate(order)}

            for b, lb in zip(bxs, labels):
                b["col_id"] = remap[lb]

            grouped = defaultdict(list)
            for b in bxs:
                grouped[b["col_id"]].append(b)

        return boxes