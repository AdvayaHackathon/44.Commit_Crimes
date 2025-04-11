import os
import logging
import numpy as np
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.database import DocumentChunk, get_db

# Set up logging
logger = logging.getLogger(__name__)

# Default embedding dimensions
EMBEDDING_DIMENSIONS = 1536  # OpenAI's embedding dimensions

# Try to import OpenAI for embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not available. Using mock embeddings.")
    OPENAI_AVAILABLE = False

# Try to import sentence-transformers as fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers package not available. Using random embeddings as fallback.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Initialize embedding model
embedding_model = None

def initialize_embedding_model():
    """Initialize the embedding model based on available packages"""
    global embedding_model

    if OPENAI_AVAILABLE:
        # Use OpenAI embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            embedding_model = OpenAI(api_key=api_key)
            logger.info("Using OpenAI for embeddings")
            return
        else:
            logger.warning("OpenAI API key not found")

    if SENTENCE_TRANSFORMERS_AVAILABLE:
        # Use sentence-transformers as fallback
        model_name = "all-MiniLM-L6-v2"  # Smaller, faster model
        embedding_model = SentenceTransformer(model_name)
        logger.info(f"Using sentence-transformers model: {model_name}")
        return

    # If no embedding model is available, we'll use random embeddings
    logger.warning("No embedding model available. Using random embeddings.")
    embedding_model = None

def get_embedding(text: str) -> List[float]:
    """Get embedding for a text string"""
    if embedding_model is None:
        initialize_embedding_model()

    if embedding_model is None:
        # Use random embeddings as fallback
        return list(np.random.normal(0, 0.1, EMBEDDING_DIMENSIONS))

    try:
        if OPENAI_AVAILABLE and isinstance(embedding_model, OpenAI):
            # Use OpenAI embeddings
            response = embedding_model.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding

        elif SENTENCE_TRANSFORMERS_AVAILABLE:
            # Use sentence-transformers
            embedding = embedding_model.encode(text)
            # Normalize to unit length
            embedding = embedding / np.linalg.norm(embedding)
            # Pad or truncate to match expected dimensions
            if len(embedding) < EMBEDDING_DIMENSIONS:
                padding = np.zeros(EMBEDDING_DIMENSIONS - len(embedding))
                embedding = np.concatenate([embedding, padding])
            elif len(embedding) > EMBEDDING_DIMENSIONS:
                embedding = embedding[:EMBEDDING_DIMENSIONS]
            return embedding.tolist()

    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        # Return random embedding as fallback
        return list(np.random.normal(0, 0.1, EMBEDDING_DIMENSIONS))

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks of approximately chunk_size characters

    Args:
        text: The text to split
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0

    while start < len(text):
        # Find the end of the chunk
        end = start + chunk_size

        if end >= len(text):
            # Last chunk
            chunks.append(text[start:])
            break

        # Try to find a good breaking point (newline or period followed by space)
        # Look for a newline first
        newline_pos = text.rfind('\n', start, end)
        if newline_pos > start + chunk_size // 2:
            # Found a good newline break point
            end = newline_pos + 1
        else:
            # Look for a period followed by space
            period_pos = text.rfind('. ', start, end)
            if period_pos > start + chunk_size // 2:
                # Found a good sentence break point
                end = period_pos + 2

        chunks.append(text[start:end])

        # Move start position for next chunk, accounting for overlap
        start = end - overlap

    return chunks

def generate_file_id(file_path: str, file_content: Optional[str] = None) -> str:
    """
    Generate a unique ID for a file based on its path and optionally its content

    Args:
        file_path: Path to the file
        file_content: Optional file content to include in the hash

    Returns:
        Unique file ID
    """
    # Create a hash of the file path
    hasher = hashlib.md5()
    hasher.update(file_path.encode('utf-8'))

    # If content is provided, include it in the hash
    if file_content:
        hasher.update(file_content.encode('utf-8'))

    return hasher.hexdigest()

def store_document_chunks(
    file_path: str,
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> List[int]:
    """
    Process a document, split it into chunks, generate embeddings, and store in the database

    Args:
        file_path: Path to the document
        text: Text content of the document
        metadata: Additional metadata about the document
        db: Database session (optional, will create one if not provided)

    Returns:
        List of chunk IDs
    """
    close_db = False
    if db is None:
        db = next(get_db())
        close_db = True

    try:
        # Generate file ID
        file_id = generate_file_id(file_path, text[:1000])  # Use first 1000 chars for hash
        file_name = os.path.basename(file_path)

        # Check if chunks for this file already exist
        existing_chunks = db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).count()
        if existing_chunks > 0:
            logger.info(f"Document {file_name} already processed with {existing_chunks} chunks")
            # Return existing chunk IDs
            chunk_ids = [chunk.id for chunk in db.query(DocumentChunk.id).filter(DocumentChunk.file_id == file_id).all()]
            return chunk_ids

        # Split text into chunks
        chunks = chunk_text(text)
        logger.info(f"Split document {file_name} into {len(chunks)} chunks")

        # Process each chunk
        chunk_ids = []
        for i, chunk_text in enumerate(chunks):
            # Generate embedding
            embedding = get_embedding(chunk_text)

            # Create chunk metadata
            chunk_metadata = {
                "chunk_index": i,
                "total_chunks": len(chunks),
                "char_start": text.find(chunk_text),
                "char_end": text.find(chunk_text) + len(chunk_text)
            }

            # Add document metadata if provided
            if metadata:
                chunk_metadata.update(metadata)

            # Create database record
            chunk = DocumentChunk(
                file_id=file_id,
                file_name=file_name,
                chunk_index=i,
                content=chunk_text,
                chunk_metadata=json.dumps(chunk_metadata),
                embedding_data=json.dumps(embedding)
            )

            db.add(chunk)
            db.flush()  # Get the ID without committing
            chunk_ids.append(chunk.id)

        # Commit all chunks
        db.commit()
        logger.info(f"Stored {len(chunks)} chunks for document {file_name}")

        return chunk_ids

    except Exception as e:
        db.rollback()
        logger.error(f"Error storing document chunks: {str(e)}")
        return []

    finally:
        if close_db:
            db.close()

def search_similar_chunks(
    query: str,
    top_k: int = 5,
    metadata_filter: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Search for chunks similar to the query text

    Args:
        query: Query text
        top_k: Number of results to return
        metadata_filter: Optional filter for metadata fields
        db: Database session (optional, will create one if not provided)

    Returns:
        List of similar chunks with similarity scores
    """
    close_db = False
    if db is None:
        db = next(get_db())
        close_db = True

    try:
        # Generate embedding for query
        query_embedding = get_embedding(query)

        # Build query
        base_query = db.query(DocumentChunk)

        # Get all chunks (we'll filter and sort manually for SQLite)
        chunks = base_query.all()

        # Filter by metadata if provided
        filtered_chunks = []
        for chunk in chunks:
            if metadata_filter:
                # Parse metadata JSON
                try:
                    chunk_meta = json.loads(chunk.chunk_metadata)
                    # Check if all filters match
                    if all(str(chunk_meta.get(key)) == str(value) for key, value in metadata_filter.items()):
                        filtered_chunks.append(chunk)
                except:
                    continue  # Skip if metadata can't be parsed
            else:
                filtered_chunks.append(chunk)

        # Calculate similarity for each chunk
        chunk_similarities = []
        for chunk in filtered_chunks:
            try:
                # Parse embedding JSON
                chunk_embedding = json.loads(chunk.embedding_data)
                # Calculate L2 distance
                l2_distance = np.linalg.norm(np.array(chunk_embedding) - np.array(query_embedding))
                # Convert to similarity score
                similarity = 1.0 / (1.0 + l2_distance)
                chunk_similarities.append((chunk, similarity))
            except:
                continue  # Skip if embedding can't be parsed

        # Sort by similarity (descending) and take top_k
        chunk_similarities.sort(key=lambda x: x[1], reverse=True)
        results = [cs[0] for cs in chunk_similarities[:top_k]]

        # Format results
        formatted_results = []
        for i, chunk in enumerate(results):
            # Get similarity from the sorted results
            if i < len(chunk_similarities):
                similarity = chunk_similarities[i][1]
            else:
                similarity = 0.0

            # Parse metadata
            try:
                metadata = json.loads(chunk.chunk_metadata)
            except:
                metadata = {}

            formatted_results.append({
                "id": chunk.id,
                "content": chunk.content,
                "metadata": metadata,
                "file_name": chunk.file_name,
                "similarity": similarity
            })

        return formatted_results

    except Exception as e:
        logger.error(f"Error searching similar chunks: {str(e)}")
        return []

    finally:
        if close_db:
            db.close()
