
def broadcast(p, r, h, sig):
    print("player[%d] broadcasts %s %s %s" % (p.i, r, h, sig))


def getstatus(contract):
    depositsL = contract.deposits(0)
    depositsR = contract.deposits(1)
    creditsL = contract.credits(0)
    creditsR = contract.credits(1)
    wdrawL = contract.withdrawals(0)
    wdrawR = contract.withdrawals(1)
    print('Status:' + ['OK','PENDING'][contract.status()])
    print('[L] deposits:' + str(depositsL) + ' credits:' + str(creditsL) + ' withdrawals:' + str(wdrawL))
    print('[R] deposits:' + str(depositsR) + ' credits:' + str(creditsR)+ ' withdrawals:' + str(wdrawR))


def completeRound(players, r, payL, payR, wdrawL, wdrawR):
    sigL = players[0].acceptInputs(r, payL, payR, wdrawL, wdrawR)
    sigR = players[1].acceptInputs(r, payL, payR, wdrawL, wdrawR)
    sigs = (sigL, sigR)
    players[0].receiveSignatures(r, sigs)
    players[1].receiveSignatures(r, sigs)
