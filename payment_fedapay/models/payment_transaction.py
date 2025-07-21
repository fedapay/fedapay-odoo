from odoo import _, models
from odoo.exceptions import ValidationError
from werkzeug import urls
from odoo.addons.payment_fedapay import const
from odoo.addons.payment_fedapay.controllers.main import FedaPayController
from odoo.addons.payment.const import CURRENCY_MINOR_UNITS

import logging, pprint

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return FedaPay-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'fedapay':
            return res

        # create transaction
        payload = self._fedapay_prepare_transaction_request_payload()
        _logger.info("sending '/transactions' request for transaction link creation:\n%s", pprint.pformat(payload))
        request_data = self.provider_id._fedapay_make_request('/transactions', data=payload)
        transaction_data = request_data.get('v1/transaction', {})

        # The provider reference is set now to allow fetching the payment status after redirection
        self.provider_reference = transaction_data.get('id')

        # Extract the checkout URL from the payment data and add it with its query parameters to the
        # rendering values. Passing the query parameters separately is necessary to prevent them
        # from being stripped off when redirecting the user to the checkout URL, which can happen
        # when only one payment method is enabled on FedaPay and query parameters are provided.
        checkout_url = transaction_data.get('payment_url')
        parsed_url = urls.url_parse(checkout_url)
        url_params = urls.url_decode(parsed_url.query)
        return {'checkout_url': checkout_url, 'url_params': url_params}
    

    def _fedapay_prepare_transaction_request_payload(self):
        """ Create the payload for the payment request based on the transaction values.

        :return: The request payload
        :rtype: dict
        """
        base_url = self.provider_id.get_base_url()
        redirect_url = urls.url_join(base_url, FedaPayController._return_url)
        decimal_places = CURRENCY_MINOR_UNITS.get(
            self.currency_id.name, self.currency_id.decimal_places
        )

        return {
            'description': f"Odoo reference : {self.reference}",
            'amount': f"{self.amount:.{decimal_places}f}",
            'currency': {
                'iso': self.currency_id.name
            },
            'callback_url': f'{redirect_url}',
        }
    
    
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on FedaPay data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'fedapay' or len(tx) == 1:
            return tx

        tx = self.search(
            [('provider_reference', '=', notification_data.get('id')), ('provider_code', '=', 'fedapay')]
        )
        _logger.info("_get_tx_from_notification_data:\n%s", pprint.pformat(notification_data))

        if not tx:
            raise ValidationError("FedaPay: " + _(
                "No transaction found matching provider reference %s.", notification_data.get('id')
            ))
        return tx


    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on FedaPay data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'fedapay':
            return

        request_data = self.provider_id._fedapay_make_request(
            f'/transactions/{self.provider_reference}', method="GET"
        )
        transaction_data = request_data.get('v1/transaction', {})

        _logger.info("sending '/transactions/search' request to retrieve transaction:\n%s", pprint.pformat(transaction_data))

        # Force FedaPay as the payment method if it exists.
        self.payment_method_id = self.env['payment.method'].search(
            [('code', '=', 'fedapay')], limit=1
        ) or self.payment_method_id

        # Update the payment state.
        payment_status = transaction_data.get('status')
        if payment_status in const.PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['canceled']:
            self._set_canceled("FedaPay: " + _("Cancelled payment with status: %s", payment_status))
        else:
            _logger.info(
                "received data with invalid payment status (%s) for transaction with reference %s",
                payment_status, self.reference
            )
            self._set_error(
                "FedaPay: " + _("Received data with invalid payment status: %s", payment_status)
            )