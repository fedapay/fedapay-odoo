# Part of Odoo. See LICENSE file for full copyright and licensing details.

API_VERSION = 'v1'  # The API version of FedaPay implemented in this module

# FedaPay proxy URL
FEDAPAY_SANDBOX_BASE_URL = 'https://sandbox-api.fedapay.com/v1'
FEDAPAY_LIVE_BASE_URL = 'https://api.fedapay.com/v1'


# Currency codes in ISO 4217 format supported by FedaPay.
# See https://docs-v1.fedapay.com/payments/currencies.
SUPPORTED_CURRENCIES = [
    'XOF',
]


# The codes of the payment methods to activate when FedaPay is activated.
DEFAULT_PAYMENT_METHOD_CODES = {
    # Primary payment method
    'fedapay',
}


# Mapping of transaction states to FedaPay payment statuses.
PAYMENT_STATUS_MAPPING = {
    'pending': ('pending',),
    'done': ('approved',),
    'canceled': ('expired', 'canceled', 'declined',)
}