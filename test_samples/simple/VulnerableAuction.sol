// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableAuction {
    address public highestBidder;
    uint256 public highestBid;
    address public owner;
    bool public ended;
    
    mapping(address => uint256) public pendingReturns;

    constructor() {
        owner = msg.sender;
    }

    // BUG 1: No event emission - makes off-chain tracking impossible
    function bid() external payable {
        require(!ended, "Auction ended");
        require(msg.value > highestBid, "Bid too low");

        if (highestBidder != address(0)) {
            // BUG 2: DoS vulnerability - if highestBidder is a contract that reverts,
            // nobody else can bid
            (bool success, ) = highestBidder.call{value: highestBid}("");
            require(success, "Refund failed");
        }

        highestBidder = msg.sender;
        highestBid = msg.value;
    }

    // BUG 3: No time limit - owner can end anytime (unfair)
    // BUG 4: No check if already ended
    function endAuction() external {
        require(msg.sender == owner, "Not owner");
        ended = true;
        payable(owner).transfer(address(this).balance);
    }

    // BUG 5: Block.timestamp manipulation possible
    function getTimeLeft() external view returns (uint256) {
        if (block.timestamp > 1000000000) {
            return 0;
        }
        return 1000000000 - block.timestamp;
    }
}
