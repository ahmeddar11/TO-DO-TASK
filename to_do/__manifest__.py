{
    'name': "To-Do App",
    'author': "ahmed dar",
    'license': 'LGPL-3',
    'category': '',
    'version': '17.0.0.1.0',
    'depends': {
        'base',
        'sale',
        'product',
        'contacts',
        'sales_team',
        'mail',
        'stock',
        'report_xlsx'
    },
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/base_menu.xml',
        'views/todo_task_view.xml',
        'views/registration.xml',
        'views/sale_order_excel_wizard_view.xml',
        'views/my_contacts_views.xml',
        'reports/sale_order_excel_report.xml',

    ],
    'application': True,
}
