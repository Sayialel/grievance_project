# Generated migration to add location field to UserProfile
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # Make sure to replace this with your actual last migration
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='location',
            field=models.CharField(choices=[('westlands', 'Westlands'), ('dagoretti_north', 'Dagoretti North'), ('langata', 'Langata'), ('kibra', 'Kibra'), ('roysambu', 'Roysambu'), ('kasarani', 'Kasarani'), ('ruaraka', 'Ruaraka'), ('embakasi_south', 'Embakasi South'), ('embakasi_north', 'Embakasi North'), ('embakasi_central', 'Embakasi Central'), ('embakasi_east', 'Embakasi East'), ('embakasi_west', 'Embakasi West'), ('makadara', 'Makadara'), ('kamukunji', 'Kamukunji'), ('starehe', 'Starehe'), ('mathare', 'Mathare'), ('other', 'Other')], default='other', max_length=50),
        ),
    ]
