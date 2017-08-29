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
    print("================TEST SCENARIO 1: HAPPY PATH")
    # Create test blockchain
    blockchain_state = tester.state()
    blockchain_state.mine()
    tester.gas_limit = 3141592

    private_keys = tester.keys[0:3]
    public_addresses = list(map(utils.privtoaddr, private_keys))

    # Create the contract
    channel_contract_code = open('channel.sol').read()
    challenge_contract_code = open('challenge.sol').read()
    contracts = init_contracts(blockchain_state, channel_contract_code, challenge_contract_code, public_addresses)
    blockchain_state.mine()

    # Create snapshots at each phase
    state_snapshots = [blockchain_state.snapshot()]

    # Initialize channel players and subnet participants
    players = init_channel_players(blockchain_state, contracts, private_keys, public_addresses)
    participants = init_subnet_participants(contracts, players, public_addresses)
    player_participant_map = dict((player, participant) for participant in participants for player in participant.player_roles)

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
        req = leader.send_set_signatures(participants[i])
        participants[i].receive_set_signatures(req)

    # Display result
    for i in range(0, 3):
        print('Triggering')
        player = players[contracts[i]][0]
        contracts[i].trigger(sender=player.sk)
        participant = player_participant_map[player]
        participant.update_after_rebalance(player.contract.address)
        blockchain_state.mine(15)

        print('Finalize')
        contracts[i].finalize()
        getstatus(contracts[i])

# Best case scenario.
def simulation_scenario_2():
    print("================TEST SCENARIO 2: UNAVAILABLE COMPLETE SIGNATURE SET FOR PARTICIPANT A")
    # Create test blockchain
    blockchain_state = tester.state()
    blockchain_state.mine()
    tester.gas_limit = 3141592

    private_keys = tester.keys[0:3]
    public_addresses = list(map(utils.privtoaddr, private_keys))

    # Create the contract
    channel_contract_code = open('channel.sol').read()
    challenge_contract_code = open('challenge.sol').read()
    contracts = init_contracts(blockchain_state, channel_contract_code, challenge_contract_code, public_addresses)
    blockchain_state.mine()

    # Create snapshots at each phase
    state_snapshots = [blockchain_state.snapshot()]

    # Initialize channel players and subnet participants
    players = init_channel_players(blockchain_state, contracts, private_keys, public_addresses)
    participants = init_subnet_participants(contracts, players, public_addresses)
    player_participant_map = dict((player, participant) for participant in participants for player in participant.player_roles)

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

    # Leader announces fully signed transaction set, but not to participant A
    for i in range(1, 3):
        req = leader.send_set_signatures(participants[i])
        participants[i].receive_set_signatures(req)

    # Participant A issues availability challenge
    participants[0].issue_challenge(contracts[0].address, wei = int(25e9 * 60e3))
    blockchain_state.mine(2)

    # Participants B, C race to respond
    participants[1].respond_to_challenge(contracts[2].address)
    participants[2].respond_to_challenge(contracts[1].address)
    blockchain_state.mine(7)

    # Display result
    for i in range(0, 3):
        print('Triggering')
        player = players[contracts[i]][0] if not i else players[contracts[i]][1]
        contracts[i].trigger(sender=player.sk)
        participant = player_participant_map[player]
        if i == 0:
            participant.update_after_rebalance_verified(player.contract.address)
        else:
            participant.update_after_rebalance(player.contract.address)
        blockchain_state.mine(15)

        print('Finalize')
        contracts[i].finalize()
        getstatus(contracts[i])


if __name__ == '__main__':
    simulation_scenario_1()
    simulation_scenario_2()


    # # Check some assertions
    # try:
    #     completeRound(players, 1, 6, 0, 0, 0) # Should fail
    # except AssertionError:
    #     pass # Should fail
    # else:
    #     raise(ValueError("Too much balance!"))