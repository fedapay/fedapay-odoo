# -*- coding: utf-8 -*-

{
    'name': 'FedaPay payment provider',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'license':'LGPL-3',
    'sequence': 350,
    'summary': 'FedaPay payment provider for Odoo',
    'description': 'Accept Visa, MasterCard, and Mobile Money payments seamlessly in Odoo with the FedaPay payment provider module.',
    'author': 'FedaPay',
    'website': 'https://www.fedapay.com',
    'depends': ['payment'],
    'data': [
        'views/payment_fedapay_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
        'data/payment_method_data.xml',      
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    "application": False,
    "images": ["static/description/banner.png"],
}