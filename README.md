# AI Knowledge Graph Assistant

A small, runnable graph-exploration app built with **Streamlit + FalkorDB + Cypher**. It stores entities and relationships, lets users explore connected knowledge, add entities, and run read-only Cypher queries.

> This repository is a starter implementation. It does not include an LLM integration or claim autonomous agent behavior. Verify the app locally and record your own demo before submitting it to a hackathon.

## Features

- Connects to FalkorDB using the Python client.
- Seeds a small sample graph with people, concepts, and technology.
- Lists graph entities and explores relationships around a selected entity.
- Adds an entity and links it to an existing entity.
- Includes a basic read-only Cypher console.
- Docker Compose setup for the database.

## Architecture

```text
Browser
  |
  v
Streamlit UI (app.py)
  |
  v
FalkorDB Python client
  |
  v
FalkorDB graph: knowledge_graph
```

## Requirements

- Python 3.10+
- Docker Desktop / Docker Engine with Docker Compose
- Internet access to install Python dependencies and pull the FalkorDB image

## Run locally

1. Download or clone this repository.
2. Start FalkorDB:

   ```bash
   docker compose up -d
   ```

3. Create and activate a virtual environment:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   streamlit run app.py
   ```

6. Open the local URL Streamlit prints (usually `http://localhost:8501`).
7. In the sidebar, click **Load / refresh demo graph**. Then explore `Python`, `Algorithms`, `Ada Lovelace`, `Alan Turing`, or `Artificial Intelligence`.

Stop the database with `docker compose down`. Data is stored in a Docker volume. To delete the volume and all graph data, run `docker compose down -v`.

## Configuration

The app reads these environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `FALKORDB_HOST` | `localhost` | FalkorDB host |
| `FALKORDB_PORT` | `6379` | FalkorDB port |
| `FALKORDB_GRAPH` | `knowledge_graph` | Graph name |

For a remote deployment, set these environment variables to the host and port provided by your FalkorDB service. Do not expose a database port publicly without authentication/network controls.

## Graph data model

The demo uses nodes with a `name`, `kind`, and optional `description`.

- `(:Person {name, kind, description})`
- `(:Concept {name, kind, description})`
- `(:Technology {name, kind, description})`
- `(:Entity {name, kind, description})` for user-created entries

Relationships include:

- `[:RELATED_TO {label}]`
- `[:USED_IN {label}]`
- User-selected types: `[:USES]`, `[:BUILDS_ON]`, `[:PART_OF]`

Example:

```text
(:Person {name: "Ada Lovelace"})
  -[:RELATED_TO {label: "wrote about"}]->
(:Concept {name: "Algorithms"})
  -[:USED_IN {label: "implemented with"}]->
(:Technology {name: "Python"})
```

## Core Cypher queries

### Seed an entity

```cypher
MERGE (:Concept {
  name: 'Algorithms',
  kind: 'Concept',
  description: 'Step-by-step procedures for solving problems'
})
```

### Create a relationship

```cypher
MATCH (a:Person {name: 'Ada Lovelace'}),
      (b:Concept {name: 'Algorithms'})
MERGE (a)-[:RELATED_TO {label: 'wrote about'}]->(b)
```

### Find direct connections to an entity

```cypher
MATCH (n {name: $name})-[r]-(m)
RETURN n.name AS source,
       type(r) AS relationship,
       coalesce(r.label, '') AS relationship_detail,
       m.name AS connected_entity,
       labels(m) AS entity_type
ORDER BY connected_entity
```

### Explore paths up to two relationships away

```cypher
MATCH p=(start {name: $name})-[*1..2]-(connected)
RETURN p
LIMIT 25
```

### List graph relationships

```cypher
MATCH (a)-[r]->(b)
RETURN a.name AS source, type(r) AS relationship, b.name AS target
LIMIT 50
```

## Demo video checklist

Record a short screen capture showing:
1. Start the database and app.
2. Load the demo graph.
3. Explore connections around `Python` and `Algorithms`.
4. Add a new entity and relationship.
5. Run the read-only Cypher query console.

Upload the recording to YouTube as **Unlisted** or **Public**, then paste that URL into the hackathon form. Do not use a placeholder link.

## Deployment

The easiest verified demo is a local run using the instructions above. For a public deployment, deploy the Streamlit app to a suitable host and connect it to a separately hosted FalkorDB instance. Configure secrets/environment variables and restrict database access. Test the public URL from a signed-out/incognito browser before submitting.

## Track guidance

The closest likely track is **Agents That Act on Connected Data** if you extend the project with actions based on retrieved graph relationships. The current starter is primarily a graph explorer; review the official track descriptions and only claim a track that matches the final working implementation.

## Limitations and next steps

- No natural-language-to-Cypher model is included.
- No authentication or multi-user access control is included.
- The graph is a demo dataset; replace it with licensed, relevant data for a real use case.
- Before public deployment, add authentication, input limits, logging, and database access controls.

## License

MIT. See `LICENSE`.
