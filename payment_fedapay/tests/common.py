# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.payment.tests.common import PaymentCommon


class FedaPayCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.fedapay = cls._prepare_provider('fedapay', update_values={
            'fedapay_sandbox_api_secret_key': 'sk_sandbox_XiLYC0gj_CTblJiCs6T4raFG',
        })
        cls.provider = cls.fedapay
        cls.currency = cls._enable_currency('XOF')

        cls.payment_data = {
            'id': '403868',
            'anount': cls.amount,
            'merchant_reference': cls.reference,
        }
