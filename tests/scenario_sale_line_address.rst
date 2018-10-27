=============
Sale Scenario
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Activate sale_line_address::

    >>> config = activate_modules('sale_line_address')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create sale user::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> sale_user = User()
    >>> sale_user.name = 'Sale'
    >>> sale_user.login = 'sale'
    >>> sale_user.main_company = company
    >>> sale_group, = Group.find([('name', '=', 'Sales')])
    >>> sale_user.groups.append(sale_group)
    >>> sale_user.save()

Create stock user::

    >>> stock_user = User()
    >>> stock_user.name = 'Stock'
    >>> stock_user.login = 'stock'
    >>> stock_user.main_company = company
    >>> stock_group, = Group.find([('name', '=', 'Stock')])
    >>> stock_user.groups.append(stock_group)
    >>> stock_user.save()

Create account user::

    >>> account_user = User()
    >>> account_user.name = 'Account'
    >>> account_user.login = 'account'
    >>> account_user.main_company = company
    >>> account_group, = Group.find([('name', '=', 'Account')])
    >>> account_user.groups.append(account_group)
    >>> account_user.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> payable = accounts['payable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> account_tax = accounts['tax']
    >>> account_cash = accounts['cash']

Create parties::

    >>> Party = Model.get('party.party')
    >>> PartyAddress = Model.get('party.address')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()
    >>> address1 = PartyAddress(name='a1', party=customer, delivery=True)
    >>> address1.save()
    >>> address2 = PartyAddress(name='a2', party=customer, delivery=True)
    >>> address2.save()
    >>> len(customer.addresses)
    3

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('5')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> product, = template.products
    >>> product.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create an Inventory::

    >>> config.user = stock_user.id
    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory.save()
    >>> inventory_line = InventoryLine(product=product, inventory=inventory)
    >>> inventory_line.quantity = 100.0
    >>> inventory_line.expected_quantity = 0.0
    >>> inventory.save()
    >>> inventory_line.save()
    >>> Inventory.confirm([inventory.id], config.context)
    >>> inventory.state
    u'done'

Sale 5 products with an invoice method 'on shipment'::

    >>> config.user = sale_user.id
    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.delivery_address = address1
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'shipment'
    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.product = product
    >>> sale_line.quantity = 2.0
    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.type = 'comment'
    >>> sale_line.description = 'Comment'
    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.product = product
    >>> sale_line.quantity = 3.0
    >>> sale_line.delivery_address = address2
    >>> sale.save()
    >>> Sale.quote([sale.id], config.context)
    >>> Sale.confirm([sale.id], config.context)
    >>> Sale.process([sale.id], config.context)
    >>> sale.state
    u'processing'
    >>> sale.reload()
    >>> len(sale.shipments), len(sale.shipment_returns), len(sale.invoices)
    (2, 0, 0)

Validate Shipments::
    >>> shipment,shipment2 = sale.shipments
    >>> config.user = stock_user.id
    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> ShipmentOut.assign_try([shipment.id], config.context)
    True
    >>> ShipmentOut.pack([shipment.id], config.context)
    >>> ShipmentOut.done([shipment.id], config.context)
    >>> ShipmentOut.assign_try([shipment2.id], config.context)
    True
    >>> ShipmentOut.pack([shipment2.id], config.context)
    >>> ShipmentOut.done([shipment2.id], config.context)

Open customer invoice::

    >>> config.user = sale_user.id
    >>> sale.reload()
    >>> len(sale.invoices)
    2
