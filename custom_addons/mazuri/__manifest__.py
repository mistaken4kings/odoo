{
    'name': 'Mazuri',
    'version': '18.0.1.1.1',
    'category': 'Sales/Sales',
    'summary': 'AI supply-chain copilot: one-click connect, catalog & inventory sync, sales orders, and embedded Pay-in-30 financing',
    'description': """
Mazuri for Odoo
===============

One app that connects your Odoo instance to the Mazuri supply-chain platform:

* **One-click connect** — authorize Mazuri from your browser, GitHub-App style.
  No manual API keys.
* **Catalog & inventory sync** — Mazuri reads products and stock levels so
  retailers can search and order your catalog in real time.
* **Sales orders** — retailer orders placed on Mazuri are pushed straight into
  Odoo Sales.
* **Embedded financing (Pay in 30)** — retailer orders financed by Mazuri are
  tracked in Odoo with disbursement, due date, and repayment status, and a
  "Mazuri Pay in 30 (interest free)" payment term is installed automatically.

Install this module, then click **Connect Odoo** in Mazuri to authorize.
    """,
    'author': 'Mazuri',
    'website': 'https://mazuri.app',
    'depends': ['base', 'web', 'sale_management', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/mazuri_connection_views.xml',
        'views/mazuri_financing_views.xml',
        'views/mazuri_menus.xml',
        'views/mazuri_connect_templates.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'post_init_hook': 'post_init_hook',
}
