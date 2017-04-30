from ethereum import tester
from ethereum import utils
from ethereum._solidity import get_solidity
SOLIDITY_AVAILABLE = get_solidity() is not None
from player import PaymentChannelPlayer
from protocol import getstatus, completeRound, init_contracts, init_channel_players, init_subnet_participants
from participant import PaymentSubnetParticipant
from leader import PaymentSubnetLeader

# Logging
from ethereum import slogging
slogging.configure(':INFO,eth.vm:INFO')

# Best case scenario.
def simulation_scenario_1():
    # Create test blockchain
    blockchain_state = tester.state()
    blockchain_state.mine()
    tester.gas_limit = 3141592

    private_keys = tester.keys[0:3]
    public_addresses = list(map(utils.privtoaddr, private_keys))

    # Create the contract
    contract_code = open('channel.sol').read()
    contracts = init_contracts(blockchain_state, contract_code, public_addresses)
    blockchain_state.mine()

    # Create snapshots at each phase
    state_snapshots = [blockchain_state.snapshot()]

    # Initialize channel players and subnet participants
    players = init_channel_players(contracts, private_keys, public_addresses)
    participants = init_subnet_participants(contracts, players, public_addresses)

    # Create initial unbalanced setting
    players[contracts[0]][0].deposit(100) # 100 A : B 0
    getstatus(contracts[0])
    players[contracts[1]][1].deposit(100) # 0   A : C 100
    getstatus(contracts[1])
    players[contracts[2]][0].deposit(100) # 100 B : C 0
    getstatus(contracts[2])

    # Save pre-rebalance snapshot
    state_snapshots.append(blockchain_state.snapshot())

    # Begin protocol, assign arbitrary leader
    leader =  PaymentSubnetLeader(participants)

    # 2 out of 3 participants signal rebalance
    for i in range(0, 2):
        req = participants[i].send_rebalance_request(leader)
        leader.receive_rebalance_request(req)

    # 2/3 >= 1/2 threshold
    assert(leader.threshold_passed)

    # Leader attempts to initiate rebalance, all participants respond
    for i in range(0, 3):
        req = leader.send_initiation_request(participants[i])
        participants[i].receive_initiation_request(req)
        resp = participants[i].send_participation_confirmation(leader)
        leader.receive_participation_confirmation(resp)

    # Leader requests channel freeze from all participants
    for i in range(0, 3):
        req = leader.send_channel_freeze_requests(participants[i])
        participants[i].receive_channel_freeze_request(req)
        resp = participants[i].send_frozen_channel_info(leader)
        leader.receive_frozen_channel_info(resp)

    # Leader generates rebalance transactions, requests signatures
    leader.generate_rebalance_set()
    for i in range(0, 3):
        req = leader.send_rebalance_transactions(participants[i])
        participants[i].receive_rebalance_transactions(req)
        resp = participants[i].send_signed_rebalance_set(leader)
        leader.receive_signed_rebalance_set(resp)

    # Leader announces fully signed transaction set
    for i in range(0, 3):
        leader.send_set_signatures(participants[i])

    # Display result
    for i in range(0, 3):
        print('Triggering')
        contracts[i].trigger(sender=players[contracts[i]][0].sk)
        players[contracts[i]][0].update()
        blockchain_state.mine(15)

        print('Finalize')
        contracts[i].finalize()
        getstatus(contracts[i])


if __name__ == '__main__':
    simulation_scenario_1()


    # # Check some assertions
    # try:
    #     completeRound(players, 1, 6, 0, 0, 0) # Should fail
    # except AssertionError:
    #     pass # Should fail
    # else:
    #     raise(ValueError("Too much balance!"))