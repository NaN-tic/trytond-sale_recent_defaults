from datetime import datetime
from trytond.model import Model, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

FIELDS = ('sale_date', 'party', 'invoice_address', 'shipment_address',
    'warehouse', 'currency', 'from_address', 'to_address', 'route',
    'invoice_method', 'shipment_method', 'pickup')

__all__ = ['Configuration', 'ConfigurationField', 'Sale']


class Configuration:
    __name__ = 'sale.configuration'
    __metaclass__ = PoolMeta

    defaults_timeout = fields.TimeDelta('Defaults Timeout', help='When the '
        'time between last creation of a sale the one being created is less '
        'than this value, several fields of the new sale will be filled in '
        'with the same values of the previous sale.')
    default_sale_fields = fields.Many2Many('sale.configuration-ir.model.field',
        'configuration', 'field', 'Default Sale Fields', domain=[
            ('model.model', '=', 'sale.sale'),
            ('ttype', 'not in', ['one2many', 'many2many']),
            ])


class ConfigurationField(ModelSQL):
    'Sale Configuration - Model Field'
    __name__ = 'sale.configuration-ir.model.field'
    configuration = fields.Many2One('sale.configuration', 'Configuration',
        required=True)
    field = fields.Many2One('ir.model.field', 'Field', required=True)


class Sale:
    __name__ = 'sale.sale'
    __metaclass__ = PoolMeta

    @classmethod
    def default_get(cls, field_names, with_rec_name=True):
        Configuration = Pool().get('sale.configuration')
        res = super(Sale, cls).default_get(field_names, with_rec_name)
        config = Configuration(1)
        timeout = config.defaults_timeout
        if timeout:
            transaction = Transaction()
            since = datetime.now() - timeout
            sales = cls.search([
                    ('company', '=', transaction.context.get('company')),
                    ('create_uid', '=', transaction.user),
                    ('create_date', '>=', since),
                    ], order=[('create_date', 'DESC')], limit=1)
            if sales:
                sale, = sales
                for field in config.default_sale_fields:
                    if field.name in field_names:
                        value = getattr(sale, field.name)
                        if isinstance(value, Model):
                            value = value.id
                        res[field.name] = value
        return res
