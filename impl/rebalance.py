from ethereum import tester
from ethereum import utils
from ethereum._solidity import get_solidity
SOLIDITY_AVAILABLE = get_solidity() is not None
from player import Player
from protocol import getstatus, broadcast, completeRound

# Logging
from ethereum import slogging
slogging.configure(':INFO,eth.vm:INFO')


# Create the simulated blockchain
s = tester.state()
s.mine()
tester.gas_limit = 3141592


keys = [tester.k1,
        tester.k2]
addrs = list(map(utils.privtoaddr, keys))

# Create the contract
contract_code = open('PaymentChannelRebalanceable.sol').read()
contract = s.abi_contract(contract_code, language='solidity',
                          constructor_parameters= ((addrs[0], addrs[1]),) )


# Take a snapshot before trying out test cases
#try: s.revert(s.snapshot())
#except: pass # FIXME: I HAVE NO IDEA WHY THIS IS REQUIRED
s.mine()
base = s.snapshot()

players = [Player(sk, i, contract, addrs) for i,sk in enumerate(keys)]

def test1():
    # Some test behaviors
    getstatus(contract)
    players[0].deposit(10)
    getstatus(contract)
    completeRound(players, 0, 5, 0, 0, 0)

    # Update
    players[0].getstatus()
    players[0].update()
    getstatus(contract)

    # Check some assertions
    try:
        completeRound(players, 1, 6, 0, 0, 0) # Should fail
    except AssertionError:
        pass # Should fail
    else:
        raise(ValueError("Too much balance!"))

    completeRound(players, 1, 0, 2, 0, 1)
    players[0].getstatus()

    print('Triggering')
    contract.trigger(sender=keys[0])
    players[0].update()
    s.mine(15)

    print('Finalize')
    contract.finalize()
    getstatus(contract)


if __name__ == '__main__':
    test1()
