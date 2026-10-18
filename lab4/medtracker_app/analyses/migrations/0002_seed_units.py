from django.db import migrations

UNITS = [
    ("ммоль/л", "концентрация"),
    ("мкмоль/л", "концентрация"),
    ("пмоль/л", "концентрация"),
    ("г/л", "концентрация"),
    ("г/дл", "концентрация"),
    ("мг/л", "концентрация"),
    ("мг/дл", "концентрация"),
    ("×10⁹/л", "количество клеток"),
    ("×10¹²/л", "количество клеток"),
    ("%", "доля"),
    ("Ед/л", "активность ферментов"),
    ("мЕд/л", "активность ферментов"),
    ("фл", "объём"),
    ("мм/ч", "скорость"),
    ("мм рт. ст.", "давление"),
    ("уд/мин", "частота"),
    ("°C", "температура"),
    ("кг", "масса"),
]


def seed_units(apps, schema_editor):
    Unit = apps.get_model("analyses", "Unit")
    for name, note in UNITS:
        Unit.objects.update_or_create(name=name, defaults={"note": note})


def unseed_units(apps, schema_editor):
    Unit = apps.get_model("analyses", "Unit")
    Unit.objects.filter(name__in=[name for name, _ in UNITS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("analyses", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_units, unseed_units),
    ]
