from ethereum import utils
from ethereum._solidity import get_solidity
SOLIDITY_AVAILABLE = get_solidity() is not None

from protocol import broadcast
from crypto import sign, verify_signature


zfill = lambda s: (32-len(s))*b'\x00' + s


def int_to_bytes(x):
    # pyethereum int to bytes does not handle negative numbers
    assert -(1<<255) <= x < (1<<255)
    return utils.int_to_bytes((1<<256) + x if x < 0 else x)


class PaymentChannelPlayer():
    def __init__(self, sk, i, contract, addrs):
        self.sk = sk
        self.i = i
        self.contract = contract
        self.addrs = addrs
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

        self.h = utils.sha3(zfill(utils.int_to_bytes(r)) +
                            zfill(int_to_bytes(creditsL)) +
                            zfill(int_to_bytes(creditsR)) +
                            zfill(utils.int_to_bytes(withdrawalsL)) +
                            zfill(utils.int_to_bytes(withdrawalsR)))
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
