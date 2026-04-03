import os
import json
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
from db.client import get_connection

load_dotenv()

client = OpenAI()

# The embedding model we're using and its maximum chunk size
EMBEDDING_MODEL = "text-embedding-3-small"
MAX_TOKENS = 500
ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count how many tokens a piece of text uses."""
    return len(ENCODING.encode(text))


def chunk_text(text: str, max_tokens: int = MAX_TOKENS) -> list:
    """
    Split a long piece of text into smaller chunks.
    We do this because embedding models have a token limit,
    and smaller chunks give more precise search results.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_tokens = 0

    for word in words:
        word_tokens = count_tokens(word)
        if current_tokens + word_tokens > max_tokens:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_tokens = word_tokens
        else:
            current_chunk.append(word)
            current_tokens += word_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def embed_text(text: str) -> list:
    """
    Send text to OpenAI and get back an embedding —
    a list of 1536 numbers that captures the meaning of the text.
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def store_document(entity_id, source_name, content, title=None, source_url=None, metadata=None):
    """
    Take a document, chunk it, embed each chunk, and store in Postgres.
    This is the main function other parts of the codebase will call.
    """
    chunks = chunk_text(content)
    print(f"Storing {len(chunks)} chunks for entity {entity_id}...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            for i, chunk in enumerate(chunks):
                embedding = embed_text(chunk)
                cur.execute("""
                    INSERT INTO documents
                        (entity_id, source_name, source_url, title,
                         content, chunk_index, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s)
                """, (
                    entity_id,
                    source_name,
                    source_url,
                    title,
                    chunk,
                    i,
                    str(embedding),
                    json.dumps(metadata or {})
                ))
        conn.commit()
    print(f"Stored {len(chunks)} chunks successfully.")


def search_documents(query: str, limit: int = 5) -> list:
    """
    Search for documents relevant to a query using vector similarity.
    Converts the query to an embedding, then finds the closest chunks.
    """
    query_embedding = embed_text(query)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT d.content, d.source_name, d.title,
                       e.canonical_name,
                       1 - (d.embedding <=> %s::vector) AS similarity
                FROM documents d
                LEFT JOIN entities e ON d.entity_id = e.id
                ORDER BY d.embedding <=> %s::vector
                LIMIT %s
            """, (str(query_embedding), str(query_embedding), limit))
            return cur.fetchall()