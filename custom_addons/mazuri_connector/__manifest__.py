{
    'name': 'Mazuri Connector',
    'version': '18.0.1.0.0',
    'category': 'Sales/Inventory',
    'summary': 'One-click connect Mazuri to your Odoo inventory and sales data',
    'description': """
Mazuri Connector lets distributors authorize Mazuri to read products,
stock levels, and push sales orders — similar to installing a GitHub App.

Install this module, then click Connect Odoo in Mazuri to authorize.
    """,
    'depends': ['stock', 'sale_management', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/mazuri_connection_views.xml',
        'views/mazuri_menus.xml',
        'views/mazuri_connect_templates.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
