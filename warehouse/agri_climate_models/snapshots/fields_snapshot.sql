{% snapshot fields_snapshot %}

{{
    config(
        target_schema='main',
        unique_key='field_id',
        strategy='check',
        check_cols=['soil_type']
    )
}}

SELECT * FROM {{ source('bronze', 'fields') }}

{% endsnapshot %}