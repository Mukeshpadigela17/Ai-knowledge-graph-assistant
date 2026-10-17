import os
import streamlit as st
from falkordb import FalkorDB
from falkordb.exceptions import FalkorDBError

st.set_page_config(page_title="AI Knowledge Graph Assistant", page_icon="🕸️", layout="wide")
st.title("🕸️ AI Knowledge Graph Assistant")
st.caption("Explore connected knowledge with FalkorDB and Cypher.")

HOST = os.getenv("FALKORDB_HOST", "localhost")
PORT = int(os.getenv("FALKORDB_PORT", "6379"))
GRAPH_NAME = os.getenv("FALKORDB_GRAPH", "knowledge_graph")

@st.cache_resource
def connect_graph():
    client = FalkorDB(host=HOST, port=PORT)
    return client.select_graph(GRAPH_NAME)

def run_query(query, params=None):
    graph = connect_graph()
    result = graph.query(query, params or {})
    headers = result.header
    rows = result.result_set
    return headers, rows

def ensure_seed_data():
    # MERGE makes this safe to run repeatedly without duplicating the demo nodes.
    queries = [
        "MERGE (:Person {name:'Ada Lovelace', kind:'Person', description:'Pioneer of early computing'})",
        "MERGE (:Person {name:'Alan Turing', kind:'Person', description:'Mathematician and computing pioneer'})",
        "MERGE (:Concept {name:'Algorithms', kind:'Concept', description:'Step-by-step procedures for solving problems'})",
        "MERGE (:Concept {name:'Artificial Intelligence', kind:'Concept', description:'Systems performing tasks associated with intelligence'})",
        "MERGE (:Technology {name:'Python', kind:'Technology', description:'General-purpose programming language'})",
        "MATCH (a:Person {name:'Ada Lovelace'}), (b:Concept {name:'Algorithms'}) MERGE (a)-[:RELATED_TO {label:'wrote about'}]->(b)",
        "MATCH (a:Person {name:'Alan Turing'}), (b:Concept {name:'Artificial Intelligence'}) MERGE (a)-[:RELATED_TO {label:'influenced'}]->(b)",
        "MATCH (a:Concept {name:'Algorithms'}), (b:Technology {name:'Python'}) MERGE (a)-[:USED_IN {label:'implemented with'}]->(b)",
        "MATCH (a:Concept {name:'Artificial Intelligence'}), (b:Technology {name:'Python'}) MERGE (a)-[:USED_IN {label:'often built with'}]->(b)",
        "MATCH (a:Person {name:'Alan Turing'}), (b:Concept {name:'Algorithms'}) MERGE (a)-[:RELATED_TO {label:'contributed to'}]->(b)",
    ]
    for q in queries:
        run_query(q)

def to_table(headers, rows):
    if not rows:
        st.info("No results returned.")
        return
    data = []
    for row in rows:
        data.append({str(headers[i].get("name", i) if isinstance(headers[i], dict) else headers[i]): str(value) for i, value in enumerate(row)})
    st.dataframe(data, use_container_width=True, hide_index=True)

with st.sidebar:
    st.subheader("Connection")
    st.write(f"Host: `{HOST}`")
    st.write(f"Port: `{PORT}`")
    st.write(f"Graph: `{GRAPH_NAME}`")
    if st.button("Load / refresh demo graph", use_container_width=True):
        try:
            ensure_seed_data()
            st.success("Demo knowledge graph is ready.")
        except Exception as exc:
            st.error(f"Could not connect to FalkorDB: {exc}")
    st.divider()
    st.caption("Start FalkorDB first. See README for setup instructions.")

tab1, tab2, tab3, tab4 = st.tabs(["Explore graph", "Add knowledge", "Cypher console", "About"])

with tab1:
    st.subheader("Find connected knowledge")
    try:
        headers, rows = run_query(
            "MATCH (n) RETURN labels(n) AS labels, n.name AS name, n.kind AS kind, n.description AS description ORDER BY name"
        )
        st.markdown("**Entities in the graph**")
        to_table(headers, rows)
    except Exception as exc:
        st.warning("FalkorDB is not reachable yet. Start it with `docker compose up -d`, then click **Load / refresh demo graph**.")
        st.caption(str(exc))

    st.markdown("**Explore relationships around an entity**")
    entity = st.text_input("Entity name", value="Python", key="explore_entity")
    if st.button("Explore connections", type="primary"):
        try:
            headers, rows = run_query(
                "MATCH (n {name:$name})-[r]-(m) RETURN n.name AS source, type(r) AS relationship, coalesce(r.label,'') AS relationship_detail, m.name AS connected_entity, labels(m) AS entity_type ORDER BY connected_entity",
                {"name": entity.strip()},
            )
            to_table(headers, rows)
            if not rows:
                st.info("No connections found. Try Python, Algorithms, Ada Lovelace, Alan Turing, or Artificial Intelligence.")
        except Exception as exc:
            st.error(f"Query failed: {exc}")

with tab2:
    st.subheader("Add an entity and connect it to existing knowledge")
    with st.form("add_entity_form"):
        name = st.text_input("Entity name", placeholder="e.g. Machine Learning")
        kind = st.selectbox("Entity type", ["Concept", "Person", "Technology", "Project", "Organization"])
        description = st.text_area("Short description", placeholder="What is this entity?")
        existing = st.text_input("Connect to existing entity", value="Python")
        relationship = st.selectbox("Relationship type", ["RELATED_TO", "USES", "BUILDS_ON", "PART_OF", "USED_IN"])
        relationship_label = st.text_input("Relationship description", value="related to")
        submitted = st.form_submit_button("Save entity and relationship", type="primary")
    if submitted:
        if not name.strip() or not existing.strip():
            st.error("Enter both entity names.")
        elif name.strip() == existing.strip():
            st.error("Choose a different existing entity.")
        else:
            try:
                # Label is selected from a fixed allowlist, while user text is passed as parameters.
                run_query(
                    "MERGE (n:Entity {name:$name}) SET n.kind=$kind, n.description=$description",
                    {"name": name.strip(), "kind": kind, "description": description.strip()},
                )
                run_query(
                    f"MATCH (a {{name:$name}}), (b {{name:$existing}}) MERGE (a)-[r:{relationship}]->(b) SET r.label=$label",
                    {"name": name.strip(), "existing": existing.strip(), "label": relationship_label.strip()},
                )
                st.success("Saved. Open Explore graph to inspect the new connection.")
            except Exception as exc:
                st.error(f"Could not save entity. Check that the connected entity exists: {exc}")

with tab3:
    st.subheader("Run a read-only Cypher query")
    st.caption("Use this console for MATCH / RETURN queries. Avoid destructive queries on important data.")
    default_query = "MATCH (a)-[r]->(b) RETURN a.name AS source, type(r) AS relationship, b.name AS target LIMIT 50"
    cypher = st.text_area("Cypher query", value=default_query, height=120)
    if st.button("Run Cypher"):
        normalized = cypher.strip().upper()
        if not normalized.startswith(("MATCH", "OPTIONAL MATCH", "WITH")) or any(word in normalized for word in [" DELETE ", " DETACH ", " CREATE ", " MERGE ", " SET "]):
            st.error("For safety, this console accepts read-only MATCH/WITH queries only. Use Add knowledge for writes.")
        else:
            try:
                headers, rows = run_query(cypher)
                to_table(headers, rows)
            except Exception as exc:
                st.error(f"Cypher error: {exc}")

with tab4:
    st.subheader("How it works")
    st.markdown("""
- **FalkorDB** stores entities as nodes and their connections as relationships.
- **Cypher** queries traverse the graph to discover direct connections.
- The app includes a small seeded example knowledge graph and a form for adding entities.
- This is a graph exploration prototype, not an LLM chatbot. An LLM can be added later to translate natural-language questions into validated Cypher.
""")
    st.code("(:Person {name:'Ada Lovelace'})-[:RELATED_TO]->(:Concept {name:'Algorithms'})", language="text")
