from player import state_to_bytes_unpack
from participant import PaymentSubnetParticipant
from typing import List
from merkle_tree import merkle_root
from ethereum import utils
from crypto import verify_signature, hash_array
from linprog import generate_transaction_set


THRESHOLD = 0.5

class PaymentSubnetLeader:
    def __init__(self, participants: List[PaymentSubnetParticipant]):
        self.subnet_participants = participants
        self.rebalance_requesters = set()
        self.threshold_passed = False
        self.potentially_participating_channels = set()
        self.participating_channels = set()
        self.possible_channel_balances = {}
        self.confirmed_channel_balances = {}
        self.rebalance_transactions = None
        self.rebalance_participants = None
        self.rebalance_signatures = {}

    def receive_rebalance_request(self, req):
        participant = req['participant']

        if participant not in self.subnet_participants:
            return False

        if participant not in self.rebalance_requesters:
            self.rebalance_requesters.add(participant)
            self.threshold_passed = len(self.rebalance_requesters) >= THRESHOLD * len(self.subnet_participants)

    def send_initiation_request(self, participant):
        return {'leader': self, 'participant': participant}

    def receive_participation_confirmation(self, req):
        assert(req['leader'] == self)
        for contract in req['contracts']:
            if contract in self.potentially_participating_channels:
                self.participating_channels.add(contract)
            else:
                self.potentially_participating_channels.add(contract)

    def send_channel_freeze_requests(self, participant: PaymentSubnetParticipant):
        req = {'leader': self, 'participant': participant, 'contracts': []}
        for player in participant.player_roles:
            if player.contract.address in self.participating_channels:
                req['contracts'].append(player.contract.address)
        return req

    def receive_frozen_channel_info(self, req):
        assert(req['leader'] == self)
        balances = req['balances']
        for contract in balances:
            if contract in self.possible_channel_balances:
                if balances[contract] != self.possible_channel_balances[contract]:
                    del self.possible_channel_balances[contract]
                else:
                    self.confirmed_channel_balances[contract] = balances[contract]
            else:
                self.possible_channel_balances[contract] = balances[contract]

    def generate_rebalance_set(self):
        self.rebalance_transactions = generate_transaction_set(self.confirmed_channel_balances)
        rebalance_participants = set()
        for participant in self.subnet_participants:
            for player in participant.player_roles:
                if player.contract.address in self.participating_channels:
                    rebalance_participants.update(player.addrs)
        self.rebalance_participants = sorted(list(rebalance_participants))

        transactions_merkle_root = merkle_root([state_to_bytes_unpack(trans) for trans in self.rebalance_transactions], utils.sha3)
        participants_hash = hash_array(self.rebalance_participants)
        self.instance_hash = utils.sha3(participants_hash + transactions_merkle_root)

    def send_rebalance_transactions(self, participant):
        return {
            'leader': self,
            'participant': participant,
            'transactions': self.rebalance_transactions,
            'participants': self.rebalance_participants
        }

    def receive_signed_rebalance_set(self, req):
        assert(req['leader'] == self)
        assert(req['participant'].public_address in self.rebalance_participants)
        assert(verify_signature(req['participant'].public_address, self.instance_hash, req['signature']))
        self.rebalance_signatures[req['participant'].public_address] = req['signature']

    def send_set_signatures(self, participant):
        return {
            'leader': self,
            'participant': participant,
            'signatures': self.rebalance_signatures,
        }