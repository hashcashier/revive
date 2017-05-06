from player import PaymentChannelPlayer
from participant import PaymentSubnetParticipant


def getstatus(contract):
    depositsL = contract.deposits(0)
    depositsR = contract.deposits(1)
    creditsL = contract.credits(0)
    creditsR = contract.credits(1)
    wdrawL = contract.withdrawals(0)
    wdrawR = contract.withdrawals(1)
    print('CONTRACT ' + str(contract.address))
    print('Status:' + ['OK','PENDING'][contract.status()])
    print('[L] deposits: ' + str(depositsL) + ' credits: ' + str(creditsL) + ' withdrawals: ' + str(wdrawL))
    print('[R] deposits: ' + str(depositsR) + ' credits: ' + str(creditsR) + ' withdrawals: ' + str(wdrawR))


def completeRound(players, r, payL, payR, wdrawL, wdrawR):
    sigL = players[0].acceptInputs(r, payL, payR, wdrawL, wdrawR)
    sigR = players[1].acceptInputs(r, payL, payR, wdrawL, wdrawR)
    sigs = (sigL, sigR)
    players[0].receiveSignatures(r, sigs)
    players[1].receiveSignatures(r, sigs)


def init_contracts(blockchain_state, channel_contract_code, challenge_contract_code, public_addresses):
    n = len(public_addresses)
    challenge_contract = blockchain_state.abi_contract(challenge_contract_code, language='solidity')
    return [blockchain_state.abi_contract(channel_contract_code,
                                          language='solidity',
                                          constructor_parameters=(challenge_contract.address, (public_addresses[i], public_addresses[j]),))
            for i in range(0, n) for j in range(i+1, n)] + [challenge_contract]


def init_channel_players(blockchain_state, contracts, private_keys, public_addresses):
    players = {}
    n = len(private_keys)
    k = 0
    for i in range(0, n):
        for j in range(i+1, n):
            players[contracts[k]] = [
                PaymentChannelPlayer(blockchain_state, private_keys[i], 0, contracts[k], [public_addresses[i], public_addresses[j]], contracts[-1]),
                PaymentChannelPlayer(blockchain_state, private_keys[j], 1, contracts[k], [public_addresses[i], public_addresses[j]], contracts[-1])]
            completeRound(players[contracts[k]], 0, 0, 0, 0, 0)
            k += 1
    return players


def init_subnet_participants(contracts, players, public_addresses):
    participant_player_roles = [list() for _ in public_addresses]
    n = len(public_addresses)
    k = 0
    for i in range(0, n):
        for j in range(i+1, n):
            participant_player_roles[i].append(players[contracts[k]][0])
            participant_player_roles[j].append(players[contracts[k]][1])
            k += 1
    return [PaymentSubnetParticipant(roles) for roles in participant_player_roles]
