from django.db import migrations


def lowercase_emails(apps, schema_editor):
    User = apps.get_model("front", "User")
    for user in User.objects.exclude(email=""):
        lowered = user.email.lower()
        if lowered != user.email:
            user.email = lowered
            user.save(update_fields=["email"])


class Migration(migrations.Migration):

    dependencies = [
        ("front", "0008_auto_20210117_1428"),
    ]

    operations = [
        migrations.RunPython(lowercase_emails, migrations.RunPython.noop),
    ]
