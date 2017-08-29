from ethereum import utils
from ethereum._solidity import get_solidity
SOLIDITY_AVAILABLE = get_solidity() is not None

from crypto import sign, verify_signature, zfill


def int_to_bytes(x):
    # pyethereum int to bytes does not handle negative numbers
    assert -(1<<255) <= x < (1<<255)
    return utils.int_to_bytes((1<<256) + x if x < 0 else x)


def broadcast(p, r, h, sig):
    print("player[%s][%d] broadcasts %s %s %s" % (p.contract.address, p.i, r, h, sig))


def state_to_bytes_unpack(args):
    return state_to_bytes(*args)

def state_to_bytes(contract, r, credits_L, credits_R, withdrawal_L, withdrawal_R):
    return contract +\
           zfill(utils.int_to_bytes(r)) +\
           zfill(int_to_bytes(credits_L)) +\
           zfill(int_to_bytes(credits_R)) +\
           zfill(utils.int_to_bytes(withdrawal_L)) +\
           zfill(utils.int_to_bytes(withdrawal_R))


class PaymentChannelPlayer():
    def __init__(self, blockchain_state, sk, i, contract, addrs, challenge_contract):
        self.blockchain_state = blockchain_state
        self.sk = sk
        self.i = i
        self.contract = contract
        self.addrs = addrs
        self.challenge_contract = challenge_contract
        self.status = "OK"
        self.lastRound = -1
        self.lastCommit = None, (0, 0, 0, 0)
        self.lastProposed = None


    def deposit(self, amt):
        self.contract.deposit(value=amt, sender=self.sk)


    def acceptInputs(self, r, payL, payR, wdrawL, wdrawR):
        assert self.status == "OK"
        assert r == self.lastRound + 1
        # Assumption - don't call acceptInputs(r,...) multiple times

        depositsL = self.contract.deposits(0)
        depositsR = self.contract.deposits(1)
        withdrawalsL = self.contract.withdrawals(0)
        withdrawalsR = self.contract.withdrawals(1)

        _, (creditsL, creditsR, withdrawnL, withdrawnR) = self.lastCommit

        assert payL <= depositsL + creditsL
        assert payR <= depositsR + creditsR
        assert wdrawL <= depositsL + creditsL - payL
        assert wdrawR <= depositsR + creditsR - payR

        creditsL += payR - payL - wdrawL
        creditsR += payL - payR - wdrawR
        withdrawalsL += wdrawL
        withdrawalsR += wdrawR

        self.lastProposed = (creditsL, creditsR, withdrawalsL, withdrawalsR)

        self.h = utils.sha3(state_to_bytes(self.contract.address, r, creditsL, creditsR, withdrawalsL, withdrawalsR))

        sig = sign(self.h, self.sk)
        broadcast(self, r, self.h, sig)
        return sig


    def receiveSignatures(self, r, sigs):
        assert self.status == "OK"
        assert r == self.lastRound + 1

        for i, sig in enumerate(sigs):
            verify_signature(self.addrs[i], self.h, sig)

        self.lastCommit = sigs, self.lastProposed
        self.lastRound += 1


    def getstatus(self):
        print('[Local view of Player %d]' % self.i)
        print('Last round:', self.lastRound)
        depositsL = self.contract.deposits(0)
        depositsR = self.contract.deposits(1)
        _, (creditsL, creditsR, wdrawL, wdrawR) = self.lastCommit
        print('Status:', self.status)
        print('[L] deposits:', depositsL, 'credits:', creditsL, 'withdrawals:', wdrawL)
        print('[R] deposits:', depositsR, 'credits:', creditsR, 'withdrawals:', wdrawR)


    def update(self):
        # Place our updated state in the contract
        sigs, (creditsL, creditsR, withdrawalsL, withdrawalsR) = self.lastCommit
        sig = sigs[1] if self.i == 0 else sigs[0]
        self.contract.update(sig, self.lastRound, (creditsL, creditsR), (withdrawalsL, withdrawalsR), sender=self.sk)

    def update_after_rebalance(self, V, R, S, participants, merkle_chain, sides):
        _, (creditsL, creditsR, withdrawalsL, withdrawalsR) = self.lastCommit
        self.contract.updateAfterRebalance(V, R, S,
                                           participants,
                                           merkle_chain,
                                           sides,
                                           self.lastRound,
                                           (creditsL, creditsR),
                                           (withdrawalsL, withdrawalsR),
                                           sender=self.sk)

    def issue_challenge(self, participants, merkle_root, wei):
        #self.blockchain_state.send(self.sk, self.challenge_contract.address, wei, [participants, merkle_root])
        self.challenge_contract.submitChallenge(participants, merkle_root, sender = self.sk, value = wei)

    def respond_to_challenge(self, V, R, S, participants, merkle_chain):
        self.challenge_contract.answerChallenge(V, R, S, participants, merkle_chain, sender = self.sk)

    def update_after_rebalance_verified(self, participants, merkle_chain, sides):
        (creditsL, creditsR, withdrawalsL, withdrawalsR) = self.lastProposed
        self.contract.updateAfterRebalanceChallenged(participants,
                                                     merkle_chain,
                                                     sides,
                                                     self.lastRound + 1,
                                                     (creditsL, creditsR),
                                                     (withdrawalsL, withdrawalsR),
                                                     sender=self.sk)
