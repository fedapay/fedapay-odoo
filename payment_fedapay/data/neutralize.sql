-- disable FedaPay payment provider
UPDATE payment_provider
   SET fedapay_live_api_secret_key = NULL,
      fedapay_sandbox_api_secret_key = NULL;
