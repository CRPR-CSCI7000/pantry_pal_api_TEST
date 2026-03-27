"""Initial migration — creates the Product model."""
import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_upc', models.CharField(db_column='productupc', max_length=20, unique=True)),
                ('product_name', models.CharField(blank=True, db_column='productname', default='', max_length=500)),
                ('product_description', models.TextField(blank=True, db_column='productdescription', default='')),
                ('product_brand', models.CharField(blank=True, db_column='productbrand', default='', max_length=255)),
                ('product_category', models.CharField(blank=True, db_column='productcategory', default='Other', max_length=100)),
                ('product_lowest_price', models.DecimalField(db_column='productlowestprice', decimal_places=2, default=0.0, max_digits=10)),
                ('product_highest_price', models.DecimalField(db_column='producthighestprice', decimal_places=2, default=0.0, max_digits=10)),
                ('product_currency', models.CharField(db_column='productcurrency', default='USD', max_length=10)),
                ('product_images', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, db_column='productimages', default=list, size=None)),
                ('product_model', models.CharField(blank=True, db_column='productmodel', default='', max_length=255)),
                ('product_color', models.CharField(blank=True, db_column='productcolor', default='', max_length=100)),
                ('product_size', models.CharField(blank=True, db_column='productsize', default='', max_length=100)),
                ('product_dimension', models.CharField(blank=True, db_column='productdimension', default='', max_length=255)),
                ('product_weight', models.CharField(blank=True, db_column='productweight', default='', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
                'db_table': 'products',
            },
        ),
    ]
