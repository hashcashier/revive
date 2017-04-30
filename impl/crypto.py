import bitcoin
from ethereum import utils

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
    arr_addr = [utils.decode_addr(x) for x in arr]
    print("ARRAY VERSIONS:")
    print(arr)
    print(arr_addr)
    print("HASH VERSIONS:")
    print(utils.sha3(arr))
    print(utils.sha3(arr_addr))
    print(utils.sha3(b''.join(arr)))
    print(utils.sha3(b''.join(arr_addr)))
    return utils.sha3(b''.join([utils.decode_addr(x) for x in arr]))