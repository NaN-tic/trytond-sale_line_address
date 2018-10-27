#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['SaleLine', 'Sale']


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    def _group_shipment_key(self, moves, move):
        res = super(Sale, self)._group_shipment_key(moves, move)
        SaleLine = Pool().get('sale.line')
        line_id, move = move
        line = SaleLine(line_id)
        return res + (('delivery_address', line.delivery_address_used.id),)


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    delivery_address = fields.Many2One('party.address', 'Delivery Address',
        domain=[('party', '=', Eval('_parent_sale', {}).get('party'))],
        depends=['type'], states={
            'invisible': Eval('type') != 'line',
            })
    delivery_address_used = fields.Function(fields.Many2One('party.address',
            'Delivery Address Used',
            states={
                'invisible': Eval('type') != 'line',
                },
            depends=['type']),
        'on_change_with_delivery_address_used')

    @fields.depends('delivery_address', 'sale', '_parent_sale.shipment_address')
    def on_change_with_delivery_address_used(self, name=None):
        if self.delivery_address:
            return self.delivery_address.id
        if not self.sale:
            return
        return (self.sale.shipment_address.id if self.sale.shipment_address
            else None)
