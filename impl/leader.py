from player import PaymentChannelPlayer
from participant import PaymentSubnetParticipant
from typing import List

THRESHOLD = 0.5

class PaymentSubnetLeader:
    def __init__(self, participants: List[PaymentSubnetParticipant]):
        self.subnet_participants = participants
        self.rebalance_requesters = set()
        self.threshold_passed = False
        self.potentially_participating_channels = set()
        self.participating_channels = set()
        self.channel_balances = {}
        self.rebalance_transactions = None

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
            if contract in self.channel_balances:
                if balances[contract] != self.channel_balances[contract]:
                    del self.channel_balances[contract]
            else:
                self.channel_balances[contract] = balances[contract]

    def generate_rebalance_set(self):
        # TODO Solve Linear Program
        pass

    def send_rebalance_transactions(self, participant):
        return {'leader': self, 'participant': participant, 'transactions': self.rebalance_transactions}

    def receive_signed_rebalance_set(self, req):
        pass

    def send_set_signatures(self, participant):
        pass
