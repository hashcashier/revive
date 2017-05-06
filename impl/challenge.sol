pragma solidity ^0.4.10;

contract RebalanceAvailabilityContract {
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
    int constant CHALLENGE_VALIDITY = 10;

    mapping ( bytes32 => int ) challenge;

    function submitChallenge(bytes32 instanceHash) {
        if (challenge[instanceHash] == 0) {
            challenge[instanceHash] = int(block.number);
        }
    }

    function answerChallenge(
            uint8[] V,
            bytes32[] R,
            bytes32[] S,
            address[] participants,
            bytes32 transactionMerkleTreeRoot) {

        bytes32 instanceHash = sha3(sha3(participants), transactionMerkleTreeRoot);

        if(challenge[instanceHash] == -1)
            return;
        else if(int(block.number) - challenge[instanceHash] > CHALLENGE_VALIDITY)
            throw;

        verifyAllSignatures(participants, instanceHash, V, R, S);

        challenge[instanceHash] = -1;
    }

    function isChallengeSuccess(bytes32 instanceHash) returns(bool) {
        return challenge[instanceHash] == -1;
    }
}