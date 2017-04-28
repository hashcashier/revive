from participant import PaymentSubnetParticipant
from typing import List


class PaymentSubnetLeader:
    def __init__(self, participants: List[PaymentSubnetParticipant]):
        self.participants = participants

    def receive_rebalance_request(self, req):
        pass

    def send_initiation_request(self):
        pass

    def receive_participation_confirmation(self, req):
        pass

    def send_channel_freeze_requests(self):
        pass

    def receive_frozen_channel_info(self, req):
        pass

    def generate_rebalance_set(self):
        pass

    def send_rebalance_transactions(self):
        pass

    def receive_signed_rebalance_set(self, req):
        pass

    def send_set_signatures(self):
        pass
