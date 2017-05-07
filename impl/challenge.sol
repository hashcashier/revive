pragma solidity ^0.4.10;

contract RebalanceAvailabilityContract {
    event LogInt(int i);
    event LogUInt(uint u);

    function verifySignature(address pub, bytes32 h, uint8 v, bytes32 r, bytes32 s) {
        if (pub != ecrecover(h,v,r,s))
            throw;
    }

    function verifyAllSignatures(address[] pub, bytes32 h, uint8[] v, bytes32[] r, bytes32[] s) {
        for (uint i = 0; i < pub.length; i++) {
            verifySignature(
                pub[i],
                h,
                v[i],      // V
                r[i],      // R
                s[i]);     // S

        }
    }


    // Challenges can be answered within 10 blocks
    uint constant CHALLENGE_VALIDITY = 10;
    uint constant GAS_PRICE_IN_WEI = 25000000000 wei;
    // 2x sha3, storage value change, storage value load, transaction, data bytes
    uint constant GAS_PER_CHALLENGE_RESPONSE = 60 + 5000 + 200 + 21000 + 68*(32);
    // sha3(address), ecrecover, data bytes
    uint constant GAS_PER_PARTICIPANT = 6 + 3000 + 68*(1 + 32*2 + 20);

    mapping ( bytes32 => int ) challenge;

    // The issued challenge is subsidized by the participant who raises it.
    function submitChallenge(
            address[] participants,
            bytes32 transactionMerkleTreeRoot) payable {

        uint response_subsidy = (GAS_PER_CHALLENGE_RESPONSE + participants.length * GAS_PER_PARTICIPANT) * GAS_PRICE_IN_WEI;

        bytes32 instanceHash = sha3(sha3(participants), transactionMerkleTreeRoot);

        if (msg.value < response_subsidy || challenge[instanceHash] != 0)
            throw;

        challenge[instanceHash] = int(block.number + CHALLENGE_VALIDITY);
    }

    function answerChallenge(
            uint8[] V,
            bytes32[] R,
            bytes32[] S,
            address[] participants,
            bytes32 transactionMerkleTreeRoot) {
        var g = msg.gas;

        bytes32 instanceHash = sha3(sha3(participants), transactionMerkleTreeRoot);

        int status = challenge[instanceHash];

        if(status == -1)
            return;
        else if(status != 0 && int(block.number) > status)
            throw;

        verifyAllSignatures(participants, instanceHash, V, R, S);

        challenge[instanceHash] = -1;

        //LogUInt(g - msg.gas);
        //LogInt(int(GAS_PER_CHALLENGE_RESPONSE + participants.length*GAS_PER_PARTICIPANT));
        if (status != 0) {
            var actual = g - msg.gas;
            var estimate = GAS_PER_CHALLENGE_RESPONSE + participants.length*GAS_PER_PARTICIPANT;
            var reimbursement = actual < estimate ? actual : estimate;
            msg.sender.transfer(reimbursement * GAS_PRICE_IN_WEI);
        }
    }

    function isChallengeSuccess(bytes32 instanceHash) returns(bool) {
        return challenge[instanceHash] == -1;
    }
}