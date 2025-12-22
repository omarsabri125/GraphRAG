class Neo4jModel:
    
    def __init__(self, db_client):
        self.db_client = db_client        

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance
    
    async def ingest_to_neo4j(self, nodes, relationships):

        async with self.db_client.session() as session:

            for node_name, node_id in nodes.items():
                await session.run(
                    "CREATE (n:Entity {name: $name, id: $id})",
                    id=node_id,
                    name=node_name
                )

            for relationship in relationships:
                await session.run(
                    "MATCH (a:Entity {id: $source_id}), (b:Entity {id: $target_id}) "
                    "CREATE (a)-[:RELATIONSHIP {type: $type}]->(b)",
                source_id = relationship["source"],
                target_id = relationship["target"],
                type = relationship["relationship"]
                )

        return nodes
        
    async def retrieve_nodes_with_id(self):

        async with self.db_client.session() as session:
            result = await session.run("MATCH (n) RETURN n.id AS uuid, n.name AS name")
            nodes = [{record["uuid"]: record["name"]} for record in result]
        
        return nodes
        
    async def fetch_related_graph(self, entity_ids):

        query = """
        MATCH (e:Entity)-[r1]-(n1)-[r2]-(n2)
        WHERE e.id IN $entity_ids
        RETURN e, r1 as r, n1 as related, r2, n2
        UNION
        MATCH (e:Entity)-[r]-(related)
        WHERE e.id IN $entity_ids
        RETURN e, r, related, null as r2, null as n2
        """
        async with self.db_client.session() as session:
            result = await session.run(query, entity_ids=entity_ids)
            subgraph = []
            for record in result:
                subgraph.append({
                    "entity": record["e"],
                    "relationship": record["r"],
                    "related_node": record["related"]
                })
                if record["r2"] and record["n2"]:
                    subgraph.append({
                        "entity": record["related"],
                        "relationship": record["r2"],
                        "related_node": record["n2"]
                    })
        return subgraph
    

    



