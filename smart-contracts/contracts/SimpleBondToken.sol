// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Simplified ERC20 interface
interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

contract SimpleBondToken is IERC20 {
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    mapping(address => bool) public kycVerified;
    
    uint256 private _totalSupply;
    string public name;
    string public symbol;
    uint8 public decimals;
    
    address public admin;
    address public issuer;
    bool public paused;
    
    // Bond-specific metadata
    string public isin;
    string public bondName;
    uint256 public faceValue;
    uint256 public couponRate; // in basis points (10000 = 100%)
    uint256 public maturityDate;
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    modifier onlyKYCVerified(address account) {
        require(kycVerified[account], "KYC not verified");
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }
    
    event KYCVerified(address indexed account);
    event KYCRevoked(address indexed account);
    event CouponDistributed(uint256 amount, uint256 timestamp);
    
    constructor(
        string memory _name,
        string memory _symbol,
        string memory _isin,
        string memory _bondName,
        uint256 _faceValue,
        uint256 _couponRate,
        uint256 _maturityDate,
        address _issuer,
        uint256 _initialSupply
    ) {
        name = _name;
        symbol = _symbol;
        decimals = 18;
        isin = _isin;
        bondName = _bondName;
        faceValue = _faceValue;
        couponRate = _couponRate;
        maturityDate = _maturityDate;
        issuer = _issuer;
        admin = msg.sender;
        
        // Mint initial supply to issuer
        _totalSupply = _initialSupply;
        _balances[_issuer] = _initialSupply;
        kycVerified[_issuer] = true;
        kycVerified[msg.sender] = true;
        
        emit Transfer(address(0), _issuer, _initialSupply);
        emit KYCVerified(_issuer);
        emit KYCVerified(msg.sender);
    }
    
    function totalSupply() public view override returns (uint256) {
        return _totalSupply;
    }
    
    function balanceOf(address account) public view override returns (uint256) {
        return _balances[account];
    }
    
    function transfer(address to, uint256 amount) public override onlyKYCVerified(msg.sender) onlyKYCVerified(to) whenNotPaused returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }
    
    function allowance(address owner, address spender) public view override returns (uint256) {
        return _allowances[owner][spender];
    }
    
    function approve(address spender, uint256 amount) public override returns (bool) {
        _approve(msg.sender, spender, amount);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) public override onlyKYCVerified(from) onlyKYCVerified(to) whenNotPaused returns (bool) {
        uint256 currentAllowance = _allowances[from][msg.sender];
        require(currentAllowance >= amount, "ERC20: transfer amount exceeds allowance");
        
        _transfer(from, to, amount);
        _approve(from, msg.sender, currentAllowance - amount);
        
        return true;
    }
    
    function _transfer(address from, address to, uint256 amount) internal {
        require(from != address(0), "ERC20: transfer from the zero address");
        require(to != address(0), "ERC20: transfer to the zero address");
        
        uint256 fromBalance = _balances[from];
        require(fromBalance >= amount, "ERC20: transfer amount exceeds balance");
        
        _balances[from] = fromBalance - amount;
        _balances[to] += amount;
        
        emit Transfer(from, to, amount);
    }
    
    function _approve(address owner, address spender, uint256 amount) internal {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");
        
        _allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }
    
    // KYC functions
    function verifyKYC(address account) external onlyAdmin {
        kycVerified[account] = true;
        emit KYCVerified(account);
    }
    
    function revokeKYC(address account) external onlyAdmin {
        kycVerified[account] = false;
        emit KYCRevoked(account);
    }
    
    // Admin functions
    function pause() external onlyAdmin {
        paused = true;
    }
    
    function unpause() external onlyAdmin {
        paused = false;
    }
    
    function mint(address to, uint256 amount) external onlyAdmin onlyKYCVerified(to) {
        _totalSupply += amount;
        _balances[to] += amount;
        emit Transfer(address(0), to, amount);
    }
    
    // Bond-specific functions
    function distributeCoupon() external onlyAdmin payable {
        require(msg.value > 0, "Coupon amount must be positive");
        
        // In a real implementation, this would distribute proportionally to all holders
        // For simplicity, we're just emitting an event
        emit CouponDistributed(msg.value, block.timestamp);
    }
    
    function getBondInfo() external view returns (
        string memory _isin,
        string memory _bondName,
        uint256 _faceValue,
        uint256 _couponRate,
        uint256 _maturityDate,
        address _issuer
    ) {
        return (isin, bondName, faceValue, couponRate, maturityDate, issuer);
    }
    
    function isMatured() external view returns (bool) {
        return block.timestamp >= maturityDate;
    }
}
