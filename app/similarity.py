from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def cluster_similar_items(items: List[Dict], similarity_threshold: float = 0.65) -> List[Dict]:
    """
    Clusters semantically similar articles using TF-IDF + cosine similarity.

    Returns one representative item per cluster.
    """

    if len(items) <= 1:
        return items

    docs = [
        f"{item.get('title','')} {item.get('description','')}"
        for item in items
    ]

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    X = vectorizer.fit_transform(docs)

    similarity_matrix = cosine_similarity(X)

    visited = set()
    clusters = []

    for i in range(len(items)):
        if i in visited:
            continue

        group = [i]
        visited.add(i)

        for j in range(i + 1, len(items)):
            if j not in visited and similarity_matrix[i][j] >= similarity_threshold:
                group.append(j)
                visited.add(j)

        clusters.append(group)

    representatives = []

    for group in clusters:
        best = max(
            group,
            key=lambda idx: len(items[idx].get("description", "")),
        )
        representatives.append(items[best])

    return representatives