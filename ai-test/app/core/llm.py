from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Tuple, List
import torch

class LocalLLM:
    def __init__(self):
        # Use the smallest possible model for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        # Force CPU to avoid CUDA issues
        self.device = 'cpu'
        self.embedding_model.to(self.device)
        # Disable gradient computation
        torch.set_grad_enabled(False)

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a text using the model."""
        with torch.no_grad():
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding

    def expand_prompt(self, prompt: str) -> str:
        """Expand a simple prompt into a more detailed description."""
        # Simple template-based expansion instead of using a language model
        templates = [
            "A detailed scene featuring {prompt}, with rich colors and textures.",
            "An artistic visualization of {prompt}, showcasing intricate details.",
            "A vivid depiction of {prompt}, highlighting its key features."
        ]
        
        # Use a simple hash of the prompt to consistently select a template
        template_index = hash(prompt) % len(templates)
        expanded_prompt = templates[template_index].format(prompt=prompt)
        
        return expanded_prompt

    def find_similar_prompts(self, prompt: str, memory_embeddings: List[np.ndarray], 
                           memory_prompts: List[str], top_k: int = 3) -> List[Tuple[str, float]]:
        """Find similar prompts from memory using embeddings."""
        if not memory_embeddings:
            return []
            
        prompt_embedding = self.get_embedding(prompt)
        memory_embeddings_array = np.array(memory_embeddings)
        
        # Calculate cosine similarity
        similarities = np.dot(memory_embeddings_array, prompt_embedding) / (
            np.linalg.norm(memory_embeddings_array, axis=1) * np.linalg.norm(prompt_embedding)
        )
        
        # Get top-k similar prompts
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [(memory_prompts[i], float(similarities[i])) for i in top_indices] 