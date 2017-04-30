from player import PaymentChannelPlayer


class PaymentSubnetParticipant:
    def __init__(self, roles = list()):
        self.player_roles = roles
        self.wants_rebalance = True # TODO This should be set as a preference at some point.
        self.frozen_channels = set()
        self.rebalance_transactions = None

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

    def send_signed_rebalance_set(self, leader):
        pass

    def receive_set_signatures(self, req):
        pass
