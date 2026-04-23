async def run(self, query: str, interests: list, duration: str) -> None:
        trace_id = gen_trace_id()
        with trace("Tour Research trace", trace_id=trace_id):
            self.printer.update_item(
                "trace_id",
                "View trace: https://platform.openai.com/traces/{}".format(trace_id),
                is_done=True,
                hide_checkmark=True,
            )
            self.printer.update_item("start", "Starting tour research...", is_done=True)

            # Get plan based on selected interests
            planner = await self._get_plan(query, interests, duration)

            # Initialize research results
            research_results = {}

            # Calculate word limits based on duration
            # Assuming average speaking rate of 150 words per minute
            words_per_minute = 150
            total_words = int(duration) * words_per_minute
            words_per_section = total_words // len(interests)

            # Only research selected interests
            if "Architecture" in interests:
                research_results["architecture"] = await self._get_architecture(query, interests, words_per_section)

            if "History" in interests:
                research_results["history"] = await self._get_history(query, interests, words_per_section)

            if "Culinary" in interests:
                research_results["culinary"] = await self._get_culinary(query, interests, words_per_section)

            if "Culture" in interests:
                research_results["culture"] = await self._get_culture(query, interests, words_per_section)

            # Get final tour with only selected interests
            final_tour = await self._get_final_tour(
                query, 
                interests, 
                duration, 
                research_results
            )

            self.printer.update_item("final_report", "", is_done=True)
            self.printer.end()

        # Build final tour content based on selected interests
        sections = []

        # Add selected interest sections without headers
        if "Architecture" in interests:
            sections.append(final_tour.architecture)
        if "History" in interests:
            sections.append(final_tour.history)
        if "Culture" in interests:
            sections.append(final_tour.culture)
        if "Culinary" in interests:
            sections.append(final_tour.culinary)

        # Format final tour with natural transitions
        final = ""
        for i, content in enumerate(sections):
            if i > 0:
                final += "\n\n"  # Add spacing between sections
            final += content

        return final