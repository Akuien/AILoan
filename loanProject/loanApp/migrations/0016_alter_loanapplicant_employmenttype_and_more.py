# Generated by Django 4.2.8 on 2023-12-16 20:08

from django.db import migrations, models
import shortuuid.main


class Migration(migrations.Migration):
    dependencies = [
        ("loanApp", "0015_alter_loanapplicant_employmenttype_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="loanapplicant",
            name="EmploymentType",
            field=models.CharField(
                choices=[
                    ("Full time", "Full-time"),
                    ("Part time", "Part-time"),
                    ("Self employed", "Self-employed"),
                    ("unemployed", "Unemployed"),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="loanapplicant",
            name="LoanID",
            field=models.CharField(
                default=shortuuid.main.ShortUUID.uuid,
                max_length=12,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]