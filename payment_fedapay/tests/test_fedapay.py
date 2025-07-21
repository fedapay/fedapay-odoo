# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon
from odoo.addons.payment_fedapay.controllers.main import FedaPayController
from odoo.addons.payment_fedapay.tests.common import FedaPayCommon


@tagged('post_install', '-at_install')
class FedaPayTest(FedaPayCommon, PaymentHttpCommon):

    def test_payment_request_payload_values(self):
        tx = self._create_transaction(flow='redirect')

        payload = tx._fedapay_prepare_payment_request_payload()

        self.assertIn('amount', payload)
        self.assertIn('currency', payload)
        self.assertIn('callback_url', payload)
        self.assertEqual(payload['description'], tx.reference)


    @mute_logger(
        'payment_fedapay.controllers.main',
        'payment_fedapay.models.payment_transaction',
    )
    def test_webhook_notification_confirms_transaction(self):
        """ Test the processing of a webhook notification. """
        tx = self._create_transaction('redirect')
        url = self._build_url(FedaPayController._webhook_url)
        with patch(
            'odoo.addons.payment_fedapay.models.payment_provider.PaymentProvider'
            '._fedapay_make_request',
            return_value={'status': 'approved'},
        ):
            self._make_http_post_request(url, data=self.notification_data)
        self.assertEqual(tx.state, 'done')