from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Utility',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(
                    choices=[
                        ('electricity', 'Electricity'),
                        ('gas', 'Gas'),
                        ('steam', 'Steam'),
                        ('air_conditioning', 'Air Conditioning')
                    ],
                    max_length=20
                )),
                ('usage', models.FloatField()),
                ('date', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
            ],
        ),
    ]
