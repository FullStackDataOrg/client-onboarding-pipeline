{# Project-level alias for dbt_utils.generate_surrogate_key.
   Lets you call {{ generate_surrogate_key([...]) }} without the package prefix
   while the Gold models still use {{ dbt_utils.generate_surrogate_key([...]) }}
   for explicit package attribution. Both resolve to the same md5 hash. #}
{%- macro generate_surrogate_key(field_list) -%}
    {{ return(dbt_utils.generate_surrogate_key(field_list)) }}
{%- endmacro -%}
