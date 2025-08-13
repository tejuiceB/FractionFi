"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Define Ethereum provider interface
interface EthereumProvider {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on?: (eventName: string, handler: (...args: unknown[]) => void) => void;
  removeListener?: (eventName: string, handler: (...args: unknown[]) => void) => void;
  isMetaMask?: boolean;
}

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

interface WalletContextType {
  isConnected: boolean;
  account: string;
  isMetaMaskInstalled: boolean;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  loading: boolean;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export const useWallet = () => {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
};

interface WalletProviderProps {
  children: ReactNode;
}

export const WalletProvider: React.FC<WalletProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [account, setAccount] = useState<string>("");
  const [isMetaMaskInstalled, setIsMetaMaskInstalled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const connectWallet = async () => {
    // Wait a bit for MetaMask to load if needed
    await new Promise(resolve => setTimeout(resolve, 100));
    
    if (!window.ethereum) {
      alert("MetaMask is not detected. Please install MetaMask extension and refresh the page.");
      window.open("https://metamask.io/download/", "_blank");
      return;
    }

    try {
      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts",
      }) as string[];
      
      if (accounts.length > 0) {
        setAccount(accounts[0]);
        setIsConnected(true);
        console.log("Connected to MetaMask:", accounts[0]);
      }
    } catch (error: unknown) {
      console.error("Failed to connect wallet:", error);
      const err = error as { code?: number; message?: string };
      if (err.code === 4001) {
        alert("Please connect to MetaMask.");
      } else {
        alert("Failed to connect to MetaMask. Please try again.");
      }
    }
  };

  const disconnectWallet = () => {
    setAccount("");
    setIsConnected(false);
  };

  useEffect(() => {
    if (!mounted) return;
    
    // Check MetaMask installation status
    const checkInstallation = () => {
      const installed = window.ethereum;
      console.log('MetaMask check:', { 
        hasEthereum: !!window.ethereum,
        isMetaMask: window.ethereum?.isMetaMask,
        installed 
      });
      setIsMetaMaskInstalled(!!installed);
      
      if (installed) {
        // Check if already connected
        window.ethereum!.request({ method: "eth_accounts" })
          .then((accounts) => {
            const accountList = accounts as string[];
            console.log('Existing accounts:', accountList);
            if (accountList.length > 0) {
              setAccount(accountList[0]);
              setIsConnected(true);
            }
          })
          .catch((error) => {
            console.error("Failed to get accounts:", error);
          })
          .finally(() => {
            setLoading(false);
          });

        // Listen for account changes
        if (window.ethereum!.on) {
          window.ethereum!.on('accountsChanged', (...args: unknown[]) => {
            const accounts = args[0] as string[];
            console.log('Account changed:', accounts);
            if (accounts.length > 0) {
              setAccount(accounts[0]);
              setIsConnected(true);
            } else {
              setAccount("");
              setIsConnected(false);
            }
          });
        }
      } else {
        setLoading(false);
      }
    };

    // Check immediately
    checkInstallation();
    
    // Also check after a short delay in case MetaMask is still loading
    setTimeout(checkInstallation, 1000);
    setTimeout(checkInstallation, 3000); // Extra check after 3 seconds
  }, [mounted]);

  const value = {
    isConnected,
    account,
    isMetaMaskInstalled,
    connectWallet,
    disconnectWallet,
    loading
  };

  return (
    <WalletContext.Provider value={value}>
      {children}
    </WalletContext.Provider>
  );
};
