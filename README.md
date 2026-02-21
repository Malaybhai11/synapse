# 🧠 Synapse
### Personal AI Research Operating System

> A stateful AI Research OS that ingests documents, tracks topics, builds structured knowledge, detects contradictions, and generates decision-grade intelligence.  
> Powered by RAG (currently in progress), it evolves into a continuous research engine with memory, hypothesis scoring, and knowledge graph intelligence.

---

# 📘 Product Requirements Document (PRD)

---

## 1. 📦 Product Overview

**Product Name:** Synapse (Working Title)  
**Category:** AI Research & Intelligence Platform  

### Current Status

| Component | Status |
|------------|--------|
| RAG Model | 🚧 In Progress |
| Research Mode | ⏳ Planned |
| Structured Memory | ⏳ Planned |
| Topic Tracking | ⏳ Planned |
| Knowledge Graph | 🔮 Future Phase |

---

## 2. 🎯 Vision

Build a stateful AI system that:

- Ingests and structures information  
- Maintains long-term memory  
- Generates actionable intelligence  
- Detects contradictions  
- Scores hypothesis confidence  
- Evolves with user behavior  

**Not a chatbot.  
A Research Operating System.**

---

## 3. 🚨 Problem Statement

Current issues in research:

- Information overload  
- Stateless AI tools  
- Fragmented notes  
- No structured memory  
- No contradiction awareness  
- No hypothesis evaluation  

Users need **decision-grade insights**, not summaries.

---

## 4. 👥 Target Users

### Phase 1
- Solo founder (internal use)

### Phase 2
- Developers  
- Indie hackers  
- Startup founders  

### Phase 3
- Analysts  
- Research-heavy teams  
- Students  

---

## 5. 🎯 Product Goals

- Reduce research time by 60–70%  
- Deliver structured outputs  
- Maintain persistent intelligence memory  
- Enable topic tracking  
- Provide confidence scoring  

---

# 🟢 Phase 1 – Intelligent Research MVP

---

## 5.1 RAG System (🚧 In Progress)

### Scope

- PDF ingestion  
- URL ingestion  
- Text ingestion  
- Chunking (500–1000 tokens)  
- Embedding generation  
- Vector storage  
- Semantic retrieval  
- Hybrid ranking (semantic + keyword)  
- Source citation enforcement  

---

## 5.2 Research Mode

### Workflow

1. Query decomposition  
2. Subtopic retrieval  
3. Multi-source synthesis  
4. Structured output generation  

### Output Includes

- Executive summary  
- Technical breakdown  
- Comparison table  
- Pros / Cons  
- Confidence score  
- Source references  

---

## 5.3 Structured Memory Layer

### A. Semantic Memory
- Vector database for embeddings  

### B. Structured Memory (PostgreSQL)

Stores:

- Insights  
- Claims  
- Topics  
- Conclusions  
- Confidence scores  
- Source IDs  

---

# 🟡 Phase 2 – Autonomous Intelligence

---

## 6.1 Topic Subscription & Tracking

- User subscribes to topic  
- Sets frequency (daily/weekly)  
- System runs scheduled search  
- Detects new information  
- Generates delta report  

---

## 6.2 Hypothesis Engine

Process:

- Reformulates user hypothesis  
- Collects supporting evidence  
- Collects opposing evidence  
- Scores evidence strength  
- Outputs structured debate + confidence  

---

## 6.3 Contradiction Detection

- Extract structured claims  
- Store embeddings  
- Compare semantic similarity  
- Detect opposite polarity  
- Flag conflicts  
- Rank credibility  

---

# 🔵 Phase 3 – Knowledge Graph

---

## 7.1 Entity Extraction

Extract:

- Concepts  
- Companies  
- Models  
- People  
- Technologies  

---

## 7.2 Relationship Mapping

Edge Types:

- `COMPETES_WITH`  
- `SUPPORTS`  
- `CONTRADICTS`  
- `USES`  
- `INSPIRED_BY`  

---

## 7.3 Graph Intelligence

Enables:

- Hidden pattern discovery  
- Idea suggestion  
- Trend clustering  
- Influence mapping  

---

# 8. ⚙️ Non-Functional Requirements

- Response time < 8 seconds  
- JSON schema enforced outputs  
- Scalable to 1M+ documents  
- Modular architecture  
- Background job reliability  
- Source traceability  
- Hallucination guardrails  

---

# 9. 🏗 Technical Architecture

---

## 9.1 Frontend

- Next.js (App Router)  
- TypeScript  
- Tailwind CSS  
- Streaming responses  
- Research dashboard  
- Topic subscription UI  

---

## 9.2 Backend

- Node.js (Fastify / Express)  
- Modular service architecture  
- BullMQ + Redis (background jobs)  
- Zod schema validation  
- REST API  

---

## 9.3 Databases

### PostgreSQL
- Users  
- Topics  
- Insights  
- Claims  
- Subscriptions  
- Logs  

### Vector Database
- Qdrant / Pinecone / Weaviate  

### Graph Database (Phase 3)
- Neo4j / Memgraph  

---

## 9.4 AI Stack

### LLM Layer
- GPT-4o / Claude / Gemini  

### Embeddings
- BGE-large  
- E5  
- OpenAI embeddings  

### Future Enhancements
- LoRA fine-tuning for personalization  

---

# 10. 🧩 Core System Components

1. Ingestion Service  
2. Embedding Service  
3. Retrieval Engine  
4. Research Orchestrator  
5. Memory Manager  
6. Hypothesis Engine  
7. Tracking Scheduler  
8. Graph Builder  
9. Output Formatter  

---

# 11. 🔄 Data Flow

User Query
    ↓
Decomposition
    ↓
Retrieval
    ↓
Synthesis
    ↓
Structured Output
    ↓
Memory Storage
    ↓
Graph Update


---

# 12. ⚠️ Risks

- Hallucinations  
- Overengineering  
- LLM cost scaling  
- Vector DB scaling  
- Background job failures  

### Mitigation

- Strict schema validation  
- Retrieval grounding  
- Caching  
- Monitoring  
- Rate limiting  

---

# 13. 📊 Success Metrics

- Weekly active users  
- Research mode usage %  
- Topic subscriptions per user  
- 30-day retention  
- Insight reuse rate  

---

# 14. 🗓 Estimated Timeline

| Phase | Timeline |
|--------|----------|
| Phase 1 | 3–4 weeks |
| Phase 2 | +4 weeks |
| Phase 3 | +4–6 weeks |

**Full system build:** ~3–4 months focused execution  

---

# 15. 🚀 Long-Term Vision

- Personal Research OS  
- Founder Intelligence Engine  
- AI Knowledge Infrastructure  
- SaaS Intelligence Platform  

---

> Synapse is not a chatbot.  
> It is an intelligence engine that compounds over time.