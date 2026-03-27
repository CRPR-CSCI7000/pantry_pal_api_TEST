"""Initial migration — creates the PantryItem model."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PantryItem',
            fields=[
                ('pantry_id', models.AutoField(db_column='pantryid', primary_key=True, serialize=False)),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ('quantity_type', models.CharField(db_column='quantitytype', default='items', max_length=50)),
                ('date_purchased', models.DateField(blank=True, null=True)),
                ('expiration_date', models.DateField(blank=True, null=True)),
                ('user', models.ForeignKey(
                    db_column='userid',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pantry_items',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('product', models.ForeignKey(
                    db_column='productupc',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pantry_entries',
                    to='products.product',
                    to_field='product_upc',
                )),
            ],
            options={
                'verbose_name': 'Pantry Item',
                'verbose_name_plural': 'Pantry Items',
                'db_table': 'usersproducts',
            },
        ),
    ]
