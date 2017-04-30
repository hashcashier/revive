
def merkle_root(array, hash):
    hashes = [hash(x) for x in array]
    while len(hashes) > 1:
        neu = list()
        for i in range(0, len(hashes), 2):
            neu.append(hash(hashes[i] + hashes[i+1]))
        if len(hashes)%2 == 1:
            neu.append(hashes[-1])
        hashes = neu
    return hashes[0] if hashes else hash(b'')
