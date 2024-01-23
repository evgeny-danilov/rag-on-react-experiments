import os
import pdb
import sys
import json

from neo4j import GraphDatabase


class NeoWritter:
    def __init__(self, nodes=[], relations=[]):
        self.driver = GraphDatabase.driver(
            os.environ['NEO_DATABASE_URL'],
            auth=(os.environ['NEO_USER'], os.environ['NEO_PASSWORD'])
        )
        self.nodes = nodes
        self.relations = relations

    def run(self):
        with self.driver.session() as session:
            self._cleanup_db(session)
            self._save_nodes(session, nodes=self.nodes)
            self._save_relations(session, relations=self.relations)

        print("=== Graph saved to Neo4j database ===")
        return

    def _save_nodes(self, session, nodes):
        for node in nodes:
            session.run(
                "CALL apoc.create.node($labels, $properties)",
                labels=['All'] + node.pop('labels'),
                properties=node
            )

    def _save_relations(self, session, relations):
        for relation in relations:
            query = """
                    MATCH (source {custom_id: $source_key})
                    MATCH (destination {custom_id: $destination_key})
                    CALL apoc.create.relationship(source, $relation_type, {}, destination) YIELD rel
                    WITH rel
                    RETURN rel
                    """

            session.run(query,
                        source_key=relation['from'],
                        destination_key=relation['to'],
                        relation_type=relation['relation'])

    def _cleanup_db(self, session):
        session.run("MATCH (n) DETACH DELETE n;")
