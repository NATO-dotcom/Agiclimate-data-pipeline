{% macro convert_kg_to_tons(column_name) -%}
    ({{ column_name }} / 1000.0)
{%- endmacro %}