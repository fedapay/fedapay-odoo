# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.payment.tests.common import PaymentCommon


class FedaPayCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.fedapay = cls._prepare_provider('fedapay', update_values={
            'fedapay_sandbox_secret_key': 'pk_sandbox_wlhaeArIxFAto7B7b_ezozIz',
        })
        cls.provider = cls.fedapay
        cls.currency = cls._prepare_currency('XOF')

        cls.notification_data = {
            'id': cls.reference,
        }
