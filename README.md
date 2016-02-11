# web2py-typeahead
typeahead.js autocomplete widget for web2py

Installation
============

- Download The plugin installer (.w2p file) and install it via the web2py interface.


Usage
=====


```python
from plugin_typeahead.typeahead import TypeheadWidget

form = SQLFORM.factory(
    Field(
        'my_field_name',
        widget=TypeheadWidget(
            request,    # web2py request object
            db.table.field,    # field for autocomplete search
            id_field=db.table.id,    # use it for reference fields, id field to submit (default: None)
            query=db.table.field.contains('husky'),    # custom query for suggestions (default: None)
            limitby=(0, 10),    # limit suggestion count (default: (0, 10))
            min_length=2,    # min length for popup suggestions (default: 2)
            prefetch=True,    # Use typeahead.js prefetch (default: True)
            remote=True,    # Use typeahead.js remote (default: True)
        )
    )
)

```

