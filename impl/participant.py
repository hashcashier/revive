from merkle_tree import merkle_root
from player import PaymentChannelPlayer, state_to_bytes
from ethereum import utils
from crypto import sign, verify_signature


class PaymentSubnetParticipant:
    def __init__(self, roles = list()):
        self.player_roles = roles
        self.private_key = roles[0].sk
        self.public_address = utils.privtoaddr(self.private_key)
        self.wants_rebalance = True # TODO This should be set as a preference at some point.
        self.frozen_channels = set()
        self.rebalance_transactions = None
        self.rebalance_participants = None

    def add_payment_channel_role(self, role: PaymentChannelPlayer):
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
            resp['balances'][contract] = player.lastCommit[1:]

        return resp

    def receive_rebalance_transactions(self, req):
        assert(req['participant'] == self)
        transactions = req['transactions']
        channel_contracts = [player.contract.address for player in self.player_roles]

        for contract, round, payL, payR, wdrawL, wdrawR in transactions:
            if contract not in channel_contracts:
                continue
            # TODO Assert transaction validity

        self.transactions_merkle_root = merkle_root([state_to_bytes(trans) for trans in transactions], utils.sha3)

        self.rebalance_participants = req['participants']
        self.participants_hash = utils.sha3(b''.join(self.rebalance_participants))

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
