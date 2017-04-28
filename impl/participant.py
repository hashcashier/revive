from player import PaymentChannelPlayer


class PaymentSubnetParticipant:
    def __init__(self, roles = list()):
        self.player_roles = roles

    def add_payment_channel_role(self, role: PaymentChannelPlayer):
        self.player_roles.append(role)

    def send_rebalance_request(self, leader):
        pass

    def receive_initiation_request(self, req):
        pass

    def send_participation_confirmation(self, leader):
        pass

    def receive_channel_freeze_request(self, req):
        pass

    def send_frozen_channel_info(self, leader):
        pass

    def receive_rebalance_transactions(self, req):
        pass

    def send_signed_rebalance_set(self, leader):
        pass

    def receive_set_signatures(self, req):
        pass
