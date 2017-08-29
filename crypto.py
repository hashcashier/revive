import bitcoin
from ethereum import utils

zfill = lambda s: (32-len(s))*b'\x00' + s

def sign(h, priv):
    assert len(h) == 32
    V, R, S = bitcoin.ecdsa_raw_sign(h, priv)
    return V,R,S


def verify_signature(addr, h, V_R_S):
    V, R, S = V_R_S
    pub = bitcoin.ecdsa_raw_recover(h, (V,R,S))
    pub = bitcoin.encode_pubkey(pub, 'bin')
    addr_ = utils.sha3(pub[1:])[12:]
    assert addr_ == addr
    return True


def hash_array(arr):
    return utils.sha3(b''.join([zfill(x) for x in arr]))