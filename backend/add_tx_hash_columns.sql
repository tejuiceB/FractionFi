-- Add tx_hash column to orders table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'orders' AND column_name = 'tx_hash'
    ) THEN
        ALTER TABLE orders ADD COLUMN tx_hash VARCHAR;
        RAISE NOTICE 'Added tx_hash column to orders table';
    ELSE
        RAISE NOTICE 'tx_hash column already exists in orders table';
    END IF;
END $$;

-- Add tx_hash column to trades table if it doesn't exist  
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trades' AND column_name = 'tx_hash'
    ) THEN
        ALTER TABLE trades ADD COLUMN tx_hash VARCHAR;
        RAISE NOTICE 'Added tx_hash column to trades table';
    ELSE
        RAISE NOTICE 'tx_hash column already exists in trades table';
    END IF;
END $$;
