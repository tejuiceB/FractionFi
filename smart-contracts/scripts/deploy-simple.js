async function main() {
  console.log("Deploying SimpleBondToken contract...");
  
  // Get the ContractFactory and Signers here.
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);
  console.log("Account balance:", (await deployer.getBalance()).toString());

  // Deploy the contract
  const SimpleBondToken = await ethers.getContractFactory("SimpleBondToken");
  const bondToken = await SimpleBondToken.deploy(
    "HDFC Bond Token", // name
    "HDFC2024", // symbol
    "INE040A08025", // isin
    "HDFC Ltd 8.5% Bond 2024", // bondName
    ethers.utils.parseEther("1000"), // faceValue (1000 ETH equivalent)
    850, // couponRate (8.5% in basis points)
    Math.floor(Date.now() / 1000) + (365 * 24 * 60 * 60), // maturityDate (1 year from now)
    deployer.address, // issuer
    ethers.utils.parseEther("1000000") // initialSupply (1 million tokens)
  );

  await bondToken.deployed();
  console.log("SimpleBondToken deployed to:", bondToken.address);
  
  // Verify some initial state
  console.log("Token name:", await bondToken.name());
  console.log("Token symbol:", await bondToken.symbol());
  console.log("Total supply:", ethers.utils.formatEther(await bondToken.totalSupply()));
  console.log("Issuer balance:", ethers.utils.formatEther(await bondToken.balanceOf(deployer.address)));
  
  // Save the contract address
  const fs = require('fs');
  const contractAddress = {
    SimpleBondToken: bondToken.address
  };
  fs.writeFileSync('./deployed-contracts.json', JSON.stringify(contractAddress, null, 2));
  console.log("Contract address saved to deployed-contracts.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
