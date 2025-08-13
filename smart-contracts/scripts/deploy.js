const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying BondToken contract...");

  // Get the contract factory
  const BondToken = await ethers.getContractFactory("BondToken");

  // Bond parameters
  const isin = "INE001A01001";
  const bondName = "FractionFi Test Bond";
  const faceValue = ethers.parseUnits("1000", 18); // 1000 tokens
  const couponRate = 750; // 7.5% in basis points
  const maturityDate = Math.floor(Date.now() / 1000) + (365 * 24 * 60 * 60); // 1 year from now
  const issuer = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"; // First hardhat account
  const totalSupply = ethers.parseUnits("1000000", 18); // 1 million tokens

  // Deploy the contract
  const bondToken = await BondToken.deploy(
    isin,
    bondName,
    faceValue,
    couponRate,
    maturityDate,
    issuer,
    totalSupply
  );

  await bondToken.waitForDeployment();

  console.log("✅ BondToken deployed successfully!");
  console.log("📋 Contract Details:");
  console.log(`   Contract Address: ${await bondToken.getAddress()}`);
  console.log(`   ISIN: ${isin}`);
  console.log(`   Bond Name: ${bondName}`);
  console.log(`   Face Value: ${ethers.formatUnits(faceValue, 18)} tokens`);
  console.log(`   Coupon Rate: ${couponRate / 100}%`);
  console.log(`   Total Supply: ${ethers.formatUnits(totalSupply, 18)} tokens`);
  console.log(`   Issuer: ${issuer}`);

  // Set KYC status for test accounts
  console.log("\n🔑 Setting KYC status for test accounts...");
  const testAccounts = [
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
  ];

  for (const account of testAccounts) {
    await bondToken.setKYCStatus(account, true);
    console.log(`   ✅ KYC verified for: ${account}`);
  }

  console.log("\n🚀 Deployment complete! Contract is ready for trading.");
  
  return {
    contract: bondToken,
    address: await bondToken.getAddress(),
    isin,
    bondName
  };
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
