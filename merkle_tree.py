import merkle


def merkle_root(array, hash):
    return merkle_tree(array, hash).build()


def merkle_tree(array, hash):
    leaves = [hash(x) for x in array]
    class HashWrap:
        def __init__(self, val):
            self.val = val

        def digest(self):
            return hash(self.val)

    merkle.hash_function = HashWrap
    merkle_tree = merkle.MerkleTree(leaves, prehashed=True, raw_digests=True)
    return merkle_tree


def merkle_chain(merkle_tree, idx):
    chain = merkle_tree.get_chain(idx)
    proof = [val for (val, pos) in chain if pos not in ('SELF',)]
    sides = [pos == 'L' for (val, pos) in chain if pos not in ('SELF',)]
    return proof, sides
