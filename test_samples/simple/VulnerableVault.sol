// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableVault {
    address public owner;
    mapping(address => uint256) public deposits;
    bool public paused;

    constructor() {
        owner = msg.sender;
    }

    // BUG 1: No access control - anyone can pause/unpause
    function setPaused(bool _paused) external {
        paused = _paused;
    }

    function deposit() external payable {
        require(!paused, "Paused");
        deposits[msg.sender] += msg.value;
    }

    // BUG 2: Unchecked return value on low-level call
    function withdraw(uint256 amount) external {
        require(!paused, "Paused");
        require(deposits[msg.sender] >= amount, "Insufficient");
        
        deposits[msg.sender] -= amount;
        
        // BUG 3: Using transfer (2300 gas limit, can fail silently with some contracts)
        payable(msg.sender).transfer(amount);
    }

    // BUG 4: Owner can drain all funds - centralization risk
    function emergencyWithdraw() external {
        require(msg.sender == owner, "Not owner");
        payable(owner).transfer(address(this).balance);
    }

    // BUG 5: tx.origin authentication - phishable
    function changeOwner(address newOwner) external {
        require(tx.origin == owner, "Not owner");
        owner = newOwner;
    }
}
