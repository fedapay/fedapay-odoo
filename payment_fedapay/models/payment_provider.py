# -*- coding: utf-8 -*-

from odoo import _, models, fields, api
from odoo.addons.payment_fedapay import const
from odoo.exceptions import ValidationError

import re, logging, requests, pprint

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('fedapay', "FedaPay")], ondelete={'fedapay': 'set default'})

    fedapay_live_api_secret_key = fields.Char(
        string='Live API secret key', 
        copy=False,
        groups="base.group_system"
    )
    fedapay_sandbox_api_secret_key = fields.Char(
        string='Sandbox API secret key',
        copy=False,
    )

    #=== CONSTRAINT METHODS ===#

    @api.constrains(
        'state', 
        'fedapay_live_api_secret_key', 
        'fedapay_sandbox_api_secret_key',
    )
    def _fedapay_config_form_validation(self):
        """ Validate provider API secret key depending on the provider state

        :return: None
        :raise ValidationError: If the provider of a connected account is set in state 'test'.
        """

        pattern_live_api_secret_key = r'^sk_live_.+'
        pattern_sandbox_api_secret_key = r'^sk_sandbox_.+'

        for record in self:

            if record.code != 'fedapay':
                continue
             
            if record.state == 'test' and not record.fedapay_sandbox_api_secret_key:
                raise ValidationError(_('The sandbox API secret key is required'))
            
            if record.state  == 'enabled' and not record.fedapay_live_api_secret_key:
                raise ValidationError(_('The live API secret key is required'))
            
            if (record.state == 'test'
                and not re.match(pattern_sandbox_api_secret_key, record.fedapay_sandbox_api_secret_key)
            ): raise ValidationError(_('The sandbox API secret key must start with sk_sandbox_'))

            if (record.state == 'enabled'
                and not re.match(pattern_live_api_secret_key, record.fedapay_live_api_secret_key)
            ): raise ValidationError(_('The live API secret key must start with sk_live_'))
            

    #=== BUSINESS METHODS ===#
    
    def _fedapay_get_api_secret_key(self):
        """ Return the appropriate FedaPay API secret key depending on the provider state.

        Note: `self.ensure_one()`

        In test mode, returns the sandbox API secret key; in live mode, returns the production API secret key.
        This method is useful for injecting the API secret key into frontend templates or payloads.

        :return: The FedaPay API secret key (sandbox ou live) as a string .
        :rtype: str
        """

        self.ensure_one()

        return self.fedapay_sandbox_api_secret_key if self.state == 'test' else self.fedapay_live_api_secret_key;
    
    
    def _fedapay_make_request(self, endpoint, data=None, method='POST'):
        """
        Send a request to the FedaPay API with authentication and error handling.

        :param str endpoint: The relative API endpoint (e.g. '/transactions')
        :param dict data: The payload to send with the request
        :param str method: The HTTP method (e.g. 'POST', 'GET', 'DELETE')
        :return: The JSON response from FedaPay
        :rtype: dict
        :raise: ValidationError if any network or API error occurs
        """
        self.ensure_one()

        # Format endpoint and full URL
        endpoint = f"/{endpoint.strip('/')}"
        url = f"{self._fedapay_get_api_url()}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self._fedapay_get_api_secret_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            'X-FedaPay-Product': 'odoo-19',
            'X-FedaPay-Channel': 'web',
            "User-Agent": f"Odoo-FedaPay/{self.env['ir.module.module'].search([('name', '=', 'payment_fedapay')], limit=1).installed_version or 'dev'}",
        }

        try:
            response = requests.request(method, url, json=data, headers=headers, timeout=60)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception("FedaPay API error at %s with data:\n%s", url, pprint.pformat(data))
                error_msg = response.json().get('message', '')
                raise ValidationError(_("FedaPay error: %s") % error_msg)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach FedaPay endpoint at %s", url)
            raise ValidationError(_("FedaPay: Could not establish a connection to the API."))

        return response.json()
    

    def _fedapay_get_api_url(self):
        """ Return the base API URL for FedaPay depending on the provider state.

        If the provider state is in test mode, the sandbox endpoint
        is returned. Otherwise, the production endpoint is used.

        :return: FedaPay API base URL
        :rtype: str
        """
        self.ensure_one()
        return const.FEDAPAY_SANDBOX_BASE_URL if self.state == 'test' else const.FEDAPAY_LIVE_BASE_URL


    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'fedapay':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies
    
    
    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'fedapay':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES