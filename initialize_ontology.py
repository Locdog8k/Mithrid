#!/usr/bin/env python3
"""Initialize the Mithrid Neo4j ontology for local or VPS development.

Prerequisite:
    pip install neo4j

Connection defaults are aligned with docker-compose.yml:
    NEO4J_URI=bolt://localhost:7687
    NEO4J_AUTH=neo4j/mithridate75

All connection settings can be overridden with environment variables:
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_AUTH, NEO4J_DATABASE
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import Neo4jError, ServiceUnavailable
except ImportError as exc:  # pragma: no cover - runtime guidance
    raise SystemExit(
        "Missing dependency: neo4j\n"
        "Install it with: python3 -m pip install neo4j"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"

DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "mithridate75"
DEFAULT_DATABASE = "neo4j"

ONTOLOGY_VERSION = "0.1.0"


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    user: str
    password: str
    database: str


CONSTRAINTS: tuple[str, ...] = (
    "CREATE CONSTRAINT mithrid_person_id IF NOT EXISTS "
    "FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_domain_id IF NOT EXISTS "
    "FOR (n:Domain) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_metric_definition_id IF NOT EXISTS "
    "FOR (n:MetricDefinition) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_metric_observation_id IF NOT EXISTS "
    "FOR (n:MetricObservation) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_event_id IF NOT EXISTS "
    "FOR (n:Event) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_habit_id IF NOT EXISTS "
    "FOR (n:Habit) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_goal_id IF NOT EXISTS "
    "FOR (n:Goal) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_project_id IF NOT EXISTS "
    "FOR (n:Project) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_task_id IF NOT EXISTS "
    "FOR (n:Task) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_source_id IF NOT EXISTS "
    "FOR (n:Source) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mithrid_tag_name IF NOT EXISTS "
    "FOR (n:Tag) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT mithrid_ontology_class_name IF NOT EXISTS "
    "FOR (n:OntologyClass) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT mithrid_ontology_relationship_name IF NOT EXISTS "
    "FOR (n:OntologyRelationship) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT mithrid_ontology_id IF NOT EXISTS "
    "FOR (n:MithridOntology) REQUIRE n.id IS UNIQUE",
)

INDEXES: tuple[str, ...] = (
    "CREATE INDEX mithrid_person_name IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE INDEX mithrid_domain_name IF NOT EXISTS FOR (n:Domain) ON (n.name)",
    "CREATE INDEX mithrid_metric_definition_name IF NOT EXISTS "
    "FOR (n:MetricDefinition) ON (n.name)",
    "CREATE INDEX mithrid_metric_observation_at IF NOT EXISTS "
    "FOR (n:MetricObservation) ON (n.observedAt)",
    "CREATE INDEX mithrid_event_started_at IF NOT EXISTS FOR (n:Event) ON (n.startedAt)",
    "CREATE INDEX mithrid_event_type IF NOT EXISTS FOR (n:Event) ON (n.type)",
    "CREATE INDEX mithrid_habit_name IF NOT EXISTS FOR (n:Habit) ON (n.name)",
    "CREATE INDEX mithrid_goal_status IF NOT EXISTS FOR (n:Goal) ON (n.status)",
    "CREATE INDEX mithrid_project_status IF NOT EXISTS FOR (n:Project) ON (n.status)",
    "CREATE INDEX mithrid_task_status IF NOT EXISTS FOR (n:Task) ON (n.status)",
    "CREATE INDEX mithrid_task_due_at IF NOT EXISTS FOR (n:Task) ON (n.dueAt)",
    "CREATE INDEX mithrid_source_name IF NOT EXISTS FOR (n:Source) ON (n.name)",
    "CREATE FULLTEXT INDEX mithrid_core_text IF NOT EXISTS "
    "FOR (n:Person|Domain|MetricDefinition|Event|Habit|Goal|Project|Task|Source|Tag) "
    "ON EACH [n.name, n.description, n.notes]",
)

ONTOLOGY_CLASSES: tuple[dict[str, str], ...] = (
    {
        "name": "Person",
        "description": "The human subject whose life data is modeled in Mithrid.",
    },
    {
        "name": "Domain",
        "description": "A life area such as health, learning, work, finance, or relationships.",
    },
    {
        "name": "MetricDefinition",
        "description": "A measurable signal definition, including unit and semantic meaning.",
    },
    {
        "name": "MetricObservation",
        "description": "A timestamped value captured for a metric definition.",
    },
    {
        "name": "Event",
        "description": "A timestamped life event, activity, decision, or incident.",
    },
    {
        "name": "Habit",
        "description": "A recurring behavior tracked over time.",
    },
    {
        "name": "Goal",
        "description": "A desired outcome linked to domains, projects, habits, or metrics.",
    },
    {
        "name": "Project",
        "description": "A bounded initiative grouping tasks and outcomes.",
    },
    {
        "name": "Task",
        "description": "An actionable unit of work with status and optional due date.",
    },
    {
        "name": "Source",
        "description": "An ingestion source such as n8n, a file import, API, or manual entry.",
    },
    {
        "name": "Tag",
        "description": "A reusable keyword for classification and retrieval.",
    },
)

ONTOLOGY_RELATIONSHIPS: tuple[dict[str, str], ...] = (
    {
        "name": "HAS_DOMAIN",
        "description": "Connects a person to a life domain.",
        "from": "Person",
        "to": "Domain",
    },
    {
        "name": "TRACKS_METRIC",
        "description": "Connects a domain, habit, goal, or project to a metric definition.",
        "from": "Domain",
        "to": "MetricDefinition",
    },
    {
        "name": "OBSERVED_AS",
        "description": "Connects a metric definition to a timestamped observation.",
        "from": "MetricDefinition",
        "to": "MetricObservation",
    },
    {
        "name": "HAS_GOAL",
        "description": "Connects a person or domain to a goal.",
        "from": "Domain",
        "to": "Goal",
    },
    {
        "name": "HAS_PROJECT",
        "description": "Connects a goal or domain to a project.",
        "from": "Goal",
        "to": "Project",
    },
    {
        "name": "HAS_TASK",
        "description": "Connects a project or goal to an actionable task.",
        "from": "Project",
        "to": "Task",
    },
    {
        "name": "HAS_HABIT",
        "description": "Connects a person, domain, or goal to a recurring habit.",
        "from": "Domain",
        "to": "Habit",
    },
    {
        "name": "RECORDED_EVENT",
        "description": "Connects a person, domain, habit, project, or task to an event.",
        "from": "Person",
        "to": "Event",
    },
    {
        "name": "FROM_SOURCE",
        "description": "Connects imported observations or events to their ingestion source.",
        "from": "Event",
        "to": "Source",
    },
    {
        "name": "TAGGED_WITH",
        "description": "Connects any core entity to a tag.",
        "from": "Event",
        "to": "Tag",
    },
)


def _parse_auth_value(auth_value: str | None) -> tuple[str, str] | None:
    if not auth_value or auth_value.lower() == "none" or "/" not in auth_value:
        return None
    user, password = auth_value.split("/", 1)
    if not user or not password:
        return None
    return user, password


def _compose_auth_defaults() -> tuple[str, str] | None:
    if not COMPOSE_FILE.exists():
        return None

    match = re.search(
        r"^\s*NEO4J_AUTH:\s*[\"']?([^\"'\n#]+)[\"']?\s*$",
        COMPOSE_FILE.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    if not match:
        return None

    return _parse_auth_value(match.group(1).strip())


def load_settings() -> Neo4jSettings:
    compose_auth = _compose_auth_defaults()
    env_auth = _parse_auth_value(os.getenv("NEO4J_AUTH"))

    default_user, default_password = compose_auth or (DEFAULT_USER, DEFAULT_PASSWORD)
    auth_user, auth_password = env_auth or (default_user, default_password)

    return Neo4jSettings(
        uri=os.getenv("NEO4J_URI", DEFAULT_URI),
        user=os.getenv("NEO4J_USER", auth_user),
        password=os.getenv("NEO4J_PASSWORD", auth_password),
        database=os.getenv("NEO4J_DATABASE", DEFAULT_DATABASE),
    )


def run_statements(session, statements: Iterable[str]) -> None:
    for statement in statements:
        session.run(statement).consume()


def initialize_ontology(settings: Neo4jSettings) -> None:
    driver = GraphDatabase.driver(settings.uri, auth=(settings.user, settings.password))

    try:
        driver.verify_connectivity()
        with driver.session(database=settings.database) as session:
            run_statements(session, CONSTRAINTS)
            run_statements(session, INDEXES)
            session.execute_write(_merge_ontology_metadata)
    finally:
        driver.close()


def _merge_ontology_metadata(tx) -> None:
    tx.run(
        """
        MERGE (ontology:MithridOntology {id: $id})
        ON CREATE SET ontology.createdAt = datetime()
        SET ontology.name = $name,
            ontology.version = $version,
            ontology.description = $description,
            ontology.updatedAt = datetime()
        """,
        id="mithrid-core",
        name="Mithrid Core Ontology",
        version=ONTOLOGY_VERSION,
        description="Core ontology for personal life engineering and life data analysis.",
    ).consume()

    tx.run(
        """
        MATCH (ontology:MithridOntology {id: $ontologyId})
        UNWIND $classes AS class
        MERGE (c:OntologyClass {name: class.name})
        ON CREATE SET c.createdAt = datetime()
        SET c.description = class.description,
            c.updatedAt = datetime()
        MERGE (ontology)-[:DEFINES_CLASS]->(c)
        """,
        ontologyId="mithrid-core",
        classes=list(ONTOLOGY_CLASSES),
    ).consume()

    tx.run(
        """
        MATCH (ontology:MithridOntology {id: $ontologyId})
        UNWIND $relationships AS relationship
        MATCH (fromClass:OntologyClass {name: relationship.from})
        MATCH (toClass:OntologyClass {name: relationship.to})
        MERGE (r:OntologyRelationship {name: relationship.name})
        ON CREATE SET r.createdAt = datetime()
        SET r.description = relationship.description,
            r.from = relationship.from,
            r.to = relationship.to,
            r.updatedAt = datetime()
        MERGE (ontology)-[:DEFINES_RELATIONSHIP]->(r)
        MERGE (fromClass)-[:CAN_CONNECT_WITH {type: relationship.name}]->(toClass)
        """,
        ontologyId="mithrid-core",
        relationships=list(ONTOLOGY_RELATIONSHIPS),
    ).consume()


def main() -> int:
    settings = load_settings()
    safe_settings = (
        f"uri={settings.uri}, user={settings.user}, database={settings.database}"
    )
    print(f"Initializing Mithrid ontology ({safe_settings})")

    try:
        initialize_ontology(settings)
    except ServiceUnavailable as exc:
        print(f"Neo4j is unavailable at {settings.uri}: {exc}", file=sys.stderr)
        return 1
    except Neo4jError as exc:
        print(f"Neo4j error while initializing ontology: {exc}", file=sys.stderr)
        return 1

    print("Mithrid ontology initialization complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
