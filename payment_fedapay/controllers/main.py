# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint, json

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class FedaPayController(http.Controller):
    _return_url = '/payment/fedapay/return'
    _webhook_url = '/payment/fedapay/webhook'


    @http.route(_return_url, type='http', auth='public', methods=['GET'])
    def fedapay_return_from_checkout(self, **data):
        """ Process the notification data sent by FedaPay after redirection.

        :param dict data: The notification data (only `id`) and the transaction status (`status`)
                          embedded in the return URL
        """

        _logger.info("handling redirection from FedaPay with data:\n%s", pprint.pformat(data))
        request.env['payment.transaction'].sudo()._handle_notification_data('fedapay', data)
        return request.redirect('/payment/status')
    

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def fedapay_webhook(self, **kwargs):
        """ Process the notification data sent by FedaPay to the webhook.

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

        notification_data = data.get('entity', {})
        _logger.info("notification received from FedaPay with data:\n%s", pprint.pformat(notification_data))        
        
        try:
            request.env['payment.transaction'].sudo()._handle_notification_data('fedapay', notification_data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed
            _logger.exception("unable to handle the notification data; skipping to acknowledge")
        return ''  # Acknowledge the notification