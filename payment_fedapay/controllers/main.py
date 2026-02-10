# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pprint, json, logging

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class FedaPayController(http.Controller):
    _return_url = '/payment/fedapay/return'
    _webhook_url = '/payment/fedapay/webhook'


    @http.route(_return_url, type='http', auth='public', methods=['GET'])
    def fedapay_return_from_checkout(self, **data):
        """ Process the transaction data sent by FedaPay after redirection.

        :param dict data: The transaction data (only `id`) and the transaction status (`status`)
                          embedded in the return URL
        """

        _logger.info("handling redirection from FedaPay with data:\n%s", pprint.pformat(data))
        self._verify_and_process(data)

        return request.redirect('/payment/status')
    

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def fedapay_webhook(self, **kwargs):
        """ Process the transaction data sent by FedaPay to the webhook.

        :param dict kwargs: This is present for compatibility, but FedaPay sends data in the JSON body,
              not as URL or form parameters.
        :return: An empty string to acknowledge the notification
        :rtype: str
        """
        
        raw_body = request.httprequest.get_data(as_text=True)
        try:
            data = json.loads(raw_body)
        except Exception:
            data = {}

        fedapay_transaction = data.get('entity', {})
        _logger.info("Notification received from FedaPay with data:\n%s", pprint.pformat(fedapay_transaction))

        self._verify_and_process(fedapay_transaction)

        return ''  # Acknowledge the notification.
    

    @staticmethod
    def _verify_and_process(data):
        """Verify and process the transaction data sent by FedaPay.

        :param dict data: The transaction data.
        :return: None
        """
        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('fedapay', data)

        if not tx_sudo:
            return
                
        try:
            response_data = tx_sudo.provider_id._fedapay_make_request(
                f'/transactions/{tx_sudo.provider_reference}', 
                method="GET"
            )
            verified_transaction_data = response_data.get('v1/transaction', {})
            _logger.info("sending '/transactions/search' request to retrieve transaction:\n%s", pprint.pformat(verified_transaction_data))
        except ValidationError:
            _logger.exception("Unable to process the transaction data")
        else:
            tx_sudo._process('fedapay', verified_transaction_data)