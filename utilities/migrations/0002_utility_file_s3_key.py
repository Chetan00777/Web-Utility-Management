from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('utilities', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='utility',
            name='file_s3_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
