from qdrant_client import AsyncQdrantClient, models

from .vector import VECTOR_SIZE, deterministic_vector

COLLECTION = "ci_failures"


async def initialize(client: AsyncQdrantClient) -> None:
    if not await client.collection_exists(COLLECTION):
        await client.create_collection(
            COLLECTION,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
        )


async def ready(client: AsyncQdrantClient) -> None:
    await client.get_collection(COLLECTION)


async def index_and_search(client: AsyncQdrantClient, run_pk: int, failures: list) -> list[dict]:
    points = []
    for failure in failures:
        point_id = run_pk * 1_000_000 + failure.id
        points.append(
            models.PointStruct(
                id=point_id,
                vector=deterministic_vector(f"{failure.node_id}\n{failure.message}\n{failure.detail}"),
                payload={"run_pk": run_pk, "failure_id": failure.id, "node_id": failure.node_id},
            )
        )
    await client.upsert(COLLECTION, points=points, wait=True)
    first = points[0]
    matches = await client.query_points(COLLECTION, query=first.vector, limit=5, with_payload=True)
    return [
        {"score": item.score, "run_pk": item.payload.get("run_pk"), "node_id": item.payload.get("node_id")}
        for item in matches.points
    ]

