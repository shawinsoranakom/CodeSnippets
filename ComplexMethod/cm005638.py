def postprocess(self, model_outputs):
        inputs = model_outputs["model_inputs"]
        table = model_outputs["table"]
        outputs = model_outputs["outputs"]
        if self.type == "tapas":
            if self.aggregate:
                logits, logits_agg = outputs[:2]
                predictions = self.tokenizer.convert_logits_to_predictions(inputs, logits, logits_agg)
                answer_coordinates_batch, agg_predictions = predictions
                aggregators = {i: self.model.config.aggregation_labels[pred] for i, pred in enumerate(agg_predictions)}

                no_agg_label_index = self.model.config.no_aggregation_label_index
                aggregators_prefix = {
                    i: aggregators[i] + " > " for i, pred in enumerate(agg_predictions) if pred != no_agg_label_index
                }
            else:
                logits = outputs[0]
                predictions = self.tokenizer.convert_logits_to_predictions(inputs, logits)
                answer_coordinates_batch = predictions[0]
                aggregators = {}
                aggregators_prefix = {}
            answers = []
            for index, coordinates in enumerate(answer_coordinates_batch):
                cells = [table.iat[coordinate] for coordinate in coordinates]
                aggregator = aggregators.get(index, "")
                aggregator_prefix = aggregators_prefix.get(index, "")
                answer = {
                    "answer": aggregator_prefix + ", ".join(cells),
                    "coordinates": coordinates,
                    "cells": [table.iat[coordinate] for coordinate in coordinates],
                }
                if aggregator:
                    answer["aggregator"] = aggregator

                answers.append(answer)
            if len(answer) == 0:
                raise PipelineException("Table question answering", self.model.name_or_path, "Empty answer")
        else:
            answers = [{"answer": answer} for answer in self.tokenizer.batch_decode(outputs, skip_special_tokens=True)]

        return answers if len(answers) > 1 else answers[0]