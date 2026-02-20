import math

def cosine_similarity(p1, p2):
    

    common = set(p1.keys()) & set(p2.keys())
    if not common:
        return 0

    dot = sum(p1[g] * p2[g] for g in common)
    mag1 = math.sqrt(sum(v*v for v in p1.values()))
    mag2 = math.sqrt(sum(v*v for v in p2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0

    return dot / (mag1 * mag2)
