# Generated migration to add date_resolved field to Complaint model
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0002_complaint_assigned_officer_alter_complaint_location_and_more'),  # Corrected dependency
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='date_resolved',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
