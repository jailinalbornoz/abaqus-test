from rest_framework import serializers


def inline_serializer(*, fields, **kwargs):
    return type(
        "InlineSerializer",
        (serializers.Serializer,),
        fields,
    )(**kwargs)
