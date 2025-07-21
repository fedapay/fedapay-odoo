-- disable mollie payment provider
UPDATE payment_provider
   SET fedapay_live_secret_key = NULL,
      fedapay_sandbox_secret_key = NULL;
