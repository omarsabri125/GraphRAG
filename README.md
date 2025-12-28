# GraphRAG

A powerful Graph-based Retrieval Augmented Generation (RAG) system built with Neo4j, Qdrant vector database, semantic caching, and multiple LLM integrations.

## Overview

GraphRAG combines the power of graph databases with vector search and large language models to create an intelligent knowledge retrieval and generation system. This project leverages Neo4j for graph storage and traversal, Qdrant for hybrid vector search, semantic caching for optimized performance, and integrates with Google Gemini and Cohere LLMs for enhanced question-answering and content generation.

## Features

- **Graph Database Integration**: Utilizes Neo4j for efficient knowledge graph storage and querying
- **Hybrid Search with Qdrant**: Advanced vector search combining dense and sparse vectors for optimal retrieval
- **Semantic Caching**: Intelligent caching layer that reduces redundant LLM calls and improves response times
- **Multi-LLM Support**: Integration with Google Gemini and Cohere for diverse AI capabilities
- **Async Architecture**: Built with Python's asyncio for high-performance operations
- **Vector Embeddings**: Support for multiple embedding models for semantic understanding
- **Template Processing**: Advanced template parsing for dynamic content generation
- **Docker Support**: Containerized deployment for easy setup and scalability

## Project Structure

```
GraphRAG/
├── frontend/                # Frontend application
├── graphrag/               # Main application code
│   ├── src/
│   │   ├── controllers/    # API controllers (NLP, Process)
│   │   ├── helpers/        # Utility functions
│   │   ├── models/         # Data models (Neo4j)
│   │   ├── routes/         # API routes
│   │   ├── schemes/        # Data schemas
│   │   └── stores/         # Data storage layers
│   │       ├── llm/        # LLM provider factories
│   │       ├── templates/  # Template parsers
│   │       └── vectordb/   # Vector database providers
│   ├── main.py            # Application entry point
│   └── pipeline.py        # Data processing pipeline
├── GraphRAGDocker/        # Docker configuration
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## Prerequisites

- Python 3.8+
- Neo4j Database
- Qdrant Vector Database
- Docker (optional, for containerized deployment)
- Google Gemini API Key
- Cohere API Key

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd GraphRAG
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Create a .env file with your settings
# Neo4j Configuration
NEO4J_URI=<your-neo4j-uri>
NEO4J_USERNAME=<your-username>
NEO4J_PASSWORD=<your-password>

# Qdrant Configuration
QDRANT_URL=<your-qdrant-url>
QDRANT_API_KEY=<your-qdrant-api-key>

# LLM API Keys
GEMINI_API_KEY=<your-gemini-api-key>
COHERE_API_KEY=<your-cohere-api-key>

# Semantic Cache Settings
CACHE_ENABLED=true
CACHE_TTL=3600
SIMILARITY_THRESHOLD=0.95
```

4. Run the application:
```bash
python main.py
```

5. Run the pipeline (one-time setup):
```bash
python pipeline.py
```
This will process your documents, extract entities and relationships, and populate both Neo4j and Qdrant.

### Docker Setup

1. Build and run with Docker Compose:
```bash
cd GraphRAGDocker
docker-compose up -d
```

## Configuration

The application uses a settings management system located in `helpers.get_settings()`. Key configuration options include:

- Neo4j connection settings (URI, credentials)
- Qdrant vector database configuration
- LLM provider settings (Gemini, Cohere)
- Semantic cache configuration
- Hybrid search parameters
- Logging levels

### Qdrant Hybrid Search

The system implements hybrid search combining:
- **Dense Vectors**: Semantic embeddings for conceptual similarity
- **Sparse Vectors**: Keyword-based matching for precise retrieval
- **Fusion Strategy**: Combines both approaches for optimal results

### Semantic Caching

Semantic caching reduces latency and API costs by:
- Storing previous query-response pairs with embeddings
- Matching similar queries using vector similarity
- Returning cached responses for semantically similar questions
- Configurable similarity thresholds and TTL

### LLM Integration

**Google Gemini**:
- Used for advanced reasoning and content generation
- Supports multimodal inputs
- Configured via `GEMINI_API_KEY`

**Cohere**:
- Provides powerful embeddings and reranking
- Excellent for multilingual support
- Configured via `COHERE_API_KEY`

## Architecture

### Data Pipeline (`pipeline.py`)

The pipeline is a **one-time execution process** designed for initial data ingestion and processing:

1. **Entity Extraction**: Extracts entities from input documents using LLMs (Gemini/Cohere)
2. **Relationship Extraction**: Identifies and extracts relationships between entities
3. **Neo4j Storage**: Stores entities and relationships as a knowledge graph in Neo4j
4. **Vector Embedding**: Generates embeddings for entities and relationships
5. **Qdrant Injection**: Indexes embeddings in Qdrant for hybrid search capabilities

**Pipeline Flow**:
```
Input Documents → Entity/Relationship Extraction → Neo4j Graph Storage → Vector Embeddings → Qdrant Index
```

Once the pipeline completes, your data is:
- **Structured** in Neo4j as a knowledge graph
- **Searchable** via Qdrant with hybrid vector search
- **Ready** for RAG queries through the API endpoints

**Note**: The pipeline should only be run once during initial setup or when adding new data to the knowledge base.

The application exposes RESTful API endpoints through controllers:

- **NLP Controller**: Natural language processing operations
- **Process Controller**: Data processing and pipeline management

## Components

### Pipeline
**One-time execution script** that:
- Extracts entities and relationships from documents using LLMs
- Builds a knowledge graph in Neo4j
- Creates vector embeddings and indexes them in Qdrant
- Should be run only during initial setup or data updates

### Controllers
Handle API requests and orchestrate business logic between models and storage layers.

### Models
Define data structures and interactions with Neo4j graph database using the Neo4jModel.

### Stores
Manage different storage backends:
- **LLM**: Factory pattern for various language model providers (Gemini, Cohere)
- **VectorDB**: Qdrant vector database operations with hybrid search capabilities
- **Templates**: Dynamic template parsing and rendering
- **Semantic Cache**: Intelligent caching layer for query optimization

### Helpers
Utility functions for configuration management, logging, and common operations.

## Development

### Running in Development Mode

```bash
python main.py --dev
```

### Logging

The application uses Python's built-in logging with configurable levels:

```python
import logging
logging.basicConfig(level=logging.INFO)
```
## Acknowledgments

- Neo4j for graph database capabilities
- Qdrant for high-performance vector search
- Google Gemini for advanced LLM capabilities
- Cohere for embeddings and multilingual support
- AsyncIO for Python async support
- The open-source community for various dependencies

## Support

For issues, questions, or contributions, please open an issue in the repository.

---

**Note**: Make sure to configure all necessary environment variables and API keys before running the application.