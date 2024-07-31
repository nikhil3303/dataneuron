from typing import Dict, Tuple, List
import json
from ..api.main import call_neuron_api
from ..db_operations.database_helpers import DatabaseHelper
from ..prompts.query_refinement_prompt import query_refinement_prompt


class QueryRefiner:
    def __init__(self, context: Dict, db, context_loader):
        self.context = context
        self.db = db
        self.db_helper = DatabaseHelper(self.db.db_type, self.db)
        self.context_loader = context_loader

    def get_sample_data(self) -> str:
        sample_data = "Sample Data:\n"
        for table_name in self.context['tables']:
            try:
                result = self.db_helper.get_sample_data(table_name)
                sample_data += f"Table: {table_name}\n"
                for row in result:
                    sample_data += f"  {row}\n"
            except Exception as e:
                sample_data += f"Table: {table_name} (Error: Unable to retrieve data)\n"
        return sample_data

    def refine_query(self, user_query: str, formatted_history: str = "") -> Tuple[str, List[str], List[Dict], List[Dict]]:
        formatted_context = self.context.get('formatted_context', '')
        sample_data = self.get_sample_data()

        prompt = query_refinement_prompt(
            formatted_context, sample_data, user_query, formatted_history)
        response = call_neuron_api(prompt)

        try:
            parsed_response = json.loads(response)
            refined_query = parsed_response.get('refined_query')
            can_be_answered = parsed_response.get('can_be_answered')
            changes = parsed_response.get('changes', [])
            entities = parsed_response.get('entities', [])
        except (json.JSONDecodeError, KeyError):
            print("Error: Invalid response from LLM.")
            return None, [], [], []

        if not can_be_answered:
            exp = parsed_response.get('explanation')
            return None, exp, [], []

        if entities:
            is_valid, refined_entities, invalid_entities = self.validate_and_refine_entities(
                entities)
            if refined_entities:
                refined_query = self.further_refine_query(
                    refined_query, refined_entities)
        else:
            is_valid, refined_entities, invalid_entities = True, [], []
        return refined_query, changes, refined_entities, invalid_entities

    def further_refine_query(self, query: str, refined_entities: List[Dict]) -> str:
        for entity in refined_entities:
            matches_len = len(entity['matches'])
            if matches_len == 1:
                query = query.replace(
                    f"containing '{entity['original_value']}'",
                    f"equal to '{entity['matches'][0]}'"
                )
            elif matches_len > 1 and len(entity['matches']) < 10:
                match_list = "', '".join(entity['matches'])
                query = query.replace(
                    f"containing '{entity['original_value']}'",
                    f"in ('{match_list}')"
                )
        return query
