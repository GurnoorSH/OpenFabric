import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.neighbors import NearestNeighbors
from pathlib import Path

class Memory:
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self._init_db()
        self.vector_dim = 768  # Default dimension for BERT embeddings
        self.nn = NearestNeighbors(n_neighbors=5, metric='cosine')
        self.vectors = []
        self.ids = []

    def _init_db(self):
        """Initialize SQLite database with necessary tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                image_path TEXT,
                model_path TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_memory(self, prompt: str, image_path: Optional[str] = None, 
                  model_path: Optional[str] = None, embedding: Optional[np.ndarray] = None):
        """Add a new memory to both SQLite and nearest neighbors index."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Store in SQLite
        c.execute('''
            INSERT INTO memories (prompt, image_path, model_path, embedding)
            VALUES (?, ?, ?, ?)
        ''', (prompt, image_path, model_path, 
              embedding.tobytes() if embedding is not None else None))
        
        memory_id = c.lastrowid
        conn.commit()
        conn.close()

        # Store in nearest neighbors index if embedding is provided
        if embedding is not None:
            self.vectors.append(embedding)
            self.ids.append(memory_id)
            if len(self.vectors) > 1:
                self.nn.fit(np.array(self.vectors))

    def search_similar(self, embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar memories using nearest neighbors."""
        if len(self.vectors) == 0:
            return []

        # Search in nearest neighbors
        if len(self.vectors) > 1:
            distances, indices = self.nn.kneighbors(np.array([embedding]), n_neighbors=min(k, len(self.vectors)))
        else:
            indices = [[0]]
            distances = [[0]]

        # Get corresponding memories from SQLite
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.ids):
                memory_id = self.ids[idx]
                c.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
                row = c.fetchone()
                if row:
                    results.append({
                        'id': row[0],
                        'prompt': row[1],
                        'image_path': row[2],
                        'model_path': row[3],
                        'similarity': float(1 - distance),  # Convert distance to similarity
                        'created_at': row[5]
                    })
        
        conn.close()
        return results

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'prompt': row[1],
                'image_path': row[2],
                'model_path': row[3],
                'created_at': row[5]
            }
        return None 