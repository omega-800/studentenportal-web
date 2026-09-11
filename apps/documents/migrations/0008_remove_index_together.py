# Remove deprecated index_together in favour of Meta.indexes
# (the actual index was already transitioned by 0007_rename via RenameIndex)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "documents",
            "0007_rename_documentdownload_document_timestamp_documents_d_documen_d84a7d_idx",
        ),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name="documentdownload",
            index_together=None,
        ),
    ]
