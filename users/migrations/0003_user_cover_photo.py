from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_new_profile_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cover_photo',
            field=models.ImageField(blank=True, null=True, upload_to='cover_photos/'),
        ),
    ]
