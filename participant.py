from merkle_tree import merkle_root, merkle_tree, merkle_chain
from player import PaymentChannelPlayer, state_to_bytes_unpack
from ethereum import utils
from crypto import sign, verify_signature, hash_array


class PaymentSubnetParticipant:
    def __init__(self, roles = list()):
        self.player_roles = roles
        self.contract_player = dict([(player.contract.address, player) for player in roles])
        self.private_key = roles[0].sk
        self.public_address = utils.privtoaddr(self.private_key)
        self.wants_rebalance = True # TODO This should be set as a preference at some point.
        self.frozen_channels = set()
        self.rebalance_transactions = None
        self.rebalance_participants = None
        self.rebalance_signatures = None

    def add_payment_channel_role(self, role, PaymentChannelPlayer):
        self.player_roles.append(role)

    def send_rebalance_request(self, leader):
        self.wants_rebalance = True
        return {'leader': leader, 'participant': self}

    def receive_initiation_request(self, req):
        assert(req['participant'] == self)

    def send_participation_confirmation(self, leader):
        resp = {'leader': leader, 'participant': self, 'contracts': []}

        if self.wants_rebalance:
            resp['contracts'] = [player.contract.address for player in self.player_roles]

        return resp

    def receive_channel_freeze_request(self, req):
        # Freeze each channel such that no further off-state updates take place
        assert(req['participant'] == self)
        for contract in req['contracts']:
            self.frozen_channels.add(contract)
        pass

    def send_frozen_channel_info(self, leader):
        resp = {'leader': leader, 'participant': self, 'balances': {}}
        for player in self.player_roles:
            contract = player.contract.address
            if contract not in self.frozen_channels:
                continue
            resp['balances'][contract] = (player.addrs,
                                          player.contract.deposits(0),
                                          player.contract.deposits(1),
                                          player.lastCommit[1:],
                                          player.lastRound)

        return resp

    def receive_rebalance_transactions(self, req):
        assert(req['participant'] == self)
        self.rebalance_transactions = req['transactions']
        channel_contracts = [player.contract.address for player in self.player_roles]

        for contract, round, creditsL, creditsR, withdrawnL, withdrawnR in self.rebalance_transactions:
            if contract not in channel_contracts:
                continue
            # TODO Assert transaction validity
            player = self.contract_player[contract]
            player.lastProposed = (creditsL, creditsR, withdrawnL, withdrawnR)

        self.transactions_merkle_tree = merkle_tree([state_to_bytes_unpack(trans) for trans in self.rebalance_transactions],
                                                    utils.sha3)
        self.transactions_merkle_root = self.transactions_merkle_tree.build()

        self.rebalance_participants = sorted(list(set(req['participants'])))
        self.participants_hash = hash_array(self.rebalance_participants)

        self.instance_hash = utils.sha3(self.participants_hash + self.transactions_merkle_root)

    def send_signed_rebalance_set(self, leader):
        return {'leader': leader, 'participant': self, 'signature': sign(self.instance_hash, self.private_key)}

    def receive_set_signatures(self, req):
        assert(req['participant'] == self)
        signatures = req['signatures']
        assert(set(self.rebalance_participants).issubset(signatures.keys()))
        for public_address in signatures:
            assert(verify_signature(public_address, self.instance_hash, signatures[public_address]))
        self.rebalance_signatures = req['signatures']

        for transaction in self.rebalance_transactions:
            if transaction[0] not in self.contract_player:
                continue
            player = self.contract_player[transaction[0]]
            player.lastCommit = [], transaction[2:]
            player.lastRound += 1

    def update_after_rebalance(self, contract):
        player = self.contract_player[contract]
        V, R, S = [], [], []
        for public_address in self.rebalance_participants:
            v, r, s = self.rebalance_signatures[public_address]
            V.append(v)
            R.append(r.to_bytes(32, byteorder='big'))
            S.append(s.to_bytes(32, byteorder='big'))
            assert(verify_signature(public_address, self.instance_hash, (v,r,s)))

        idx = next(i for i, v in enumerate(self.rebalance_transactions) if v[0] == contract)
        chain, sides = merkle_chain(
            self.transactions_merkle_tree,
            idx)

        player.update_after_rebalance(V, R, S, self.rebalance_participants, chain, sides)

    def issue_challenge(self, contract, wei):
        player = self.contract_player[contract]
        idx = next(i for i, v in enumerate(self.rebalance_transactions) if v[0] == contract)
        chain, _ = merkle_chain(
            self.transactions_merkle_tree,
            idx)
        player.issue_challenge(self.rebalance_participants, chain[-1], wei)

    def respond_to_challenge(self, contract):
        player = self.contract_player[contract]
        V, R, S = [], [], []
        for public_address in self.rebalance_participants:
            v, r, s = self.rebalance_signatures[public_address]
            V.append(v)
            R.append(r.to_bytes(32, byteorder='big'))
            S.append(s.to_bytes(32, byteorder='big'))
            assert(verify_signature(public_address, self.instance_hash, (v,r,s)))

        idx = next(i for i, v in enumerate(self.rebalance_transactions) if v[0] == contract)
        chain, sides = merkle_chain(
            self.transactions_merkle_tree,
            idx)

        player.respond_to_challenge(V, R, S, self.rebalance_participants, chain[-1])

    def update_after_rebalance_verified(self, contract):
        player = self.contract_player[contract]

        idx = next(i for i, v in enumerate(self.rebalance_transactions) if v[0] == contract)
        chain, sides = merkle_chain(
            self.transactions_merkle_tree,
            idx)

        player.update_after_rebalance_verified(self.rebalance_participants, chain, sides)
