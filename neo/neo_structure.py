import pdb
import os
from typing import Dict, Optional

from neo4j import GraphDatabase


class NeoStructure:
    def __init__(self):
        self.neo_driver = GraphDatabase.driver(
            os.environ['NEO_DATABASE_URL'], auth=(os.environ['NEO_USER'], os.environ['NEO_PASSWORD'])
        )

    def schema_text(self):
        result = f"""
                Node prorerties are:
                {self._node_properties()}
                Relations are:
                {self._relations()}
                """

        self.neo_driver.close()
        return result

    def _node_properties(self):
        return self._query(self._node_properties_request())

    def _relations(self):
        return self._query(self._relations_request())

    def _query(self, query: str):
        with self.neo_driver.session() as session:
            result = session.read_transaction(self._execute_read_only_query, query)
            return result

    @staticmethod
    def _execute_read_only_query(tx, query: str, params: Optional[Dict] = {}):
        result = tx.run_script_command(query, params)
        return [r.data() for r in result]

    def _node_properties_request(self):
        """
        CALL apoc.meta.data()
        YIELD label, other, elementType, type, property
        WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
        WITH label AS nodeLabels, collect([property, type]) AS propertyTypePairs
        WITH nodeLabels, apoc.map.fromPairs(propertyTypePairs) AS properties
        RETURN {labels: nodeLabels, properties: properties} AS output
        """

    def _relations_request(self):
        """
        CALL db.relationshipTypes()
        YIELD relationshipType
        RETURN collect(relationshipType) as relationshipTypes
        """
