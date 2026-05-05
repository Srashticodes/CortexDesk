from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
import os

# 🔥 LOAD MODEL ONLY ONCE
MODEL = SentenceTransformer('all-MiniLM-L6-v2')


class Retriever:
    def __init__(self, docs, name):
        self.model = MODEL
        self.docs = docs
        self.name = name

        cache_file = f"cache_{name}.pkl"

        # ✅ LOAD EMBEDDINGS FROM CACHE (FAST)
        if os.path.exists(cache_file):
            with open(cache_file, "rb") as f:
                self.doc_embeddings = pickle.load(f)
        else:
            # ❌ Only happens first time
            self.doc_embeddings = self.model.encode(docs)

            with open(cache_file, "wb") as f:
                pickle.dump(self.doc_embeddings, f)

    def retrieve(self, query):
        query_embedding = self.model.encode([query])[0]

        similarities = np.dot(self.doc_embeddings, query_embedding)

        top_indices = similarities.argsort()[-3:][::-1]

        return [self.docs[i] for i in top_indices]