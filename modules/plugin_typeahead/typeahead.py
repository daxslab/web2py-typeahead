__author__ = 'cccaballero'
from gluon import *
from gluon import sqlhtml

StringWidget = sqlhtml.StringWidget


class TypeheadWidget(object):
    _class = 'string'

    def __init__(self, request, field, query=None, id_field=None, db=None,
                 orderby=None, limitby=(0, 9), distinct=False,
                 keyword='_plugin_typeahead_%(tablename)s_%(fieldname)s',
                 min_length=2, prefetch=True, remote=True):

        current.response.files.append(URL('static','plugin_typeahead/typeahead.bundle.min.js'))
        current.response.files.append(URL('static','plugin_typeahead/typeahead-bootstrap.css'))

        self.request = request
        self.keyword = keyword % dict(tablename=field.tablename,
                                      fieldname=field.name)
        self.prefetch = prefetch
        self.remote = remote
        self.query = query
        self.db = db or field._db
        self.orderby = orderby
        self.limitby = limitby
        self.distinct = distinct
        self.min_length = min_length
        self.fields = [field]
        self.id_field = id_field
        if id_field:
            self.is_reference = True
            self.fields.append(id_field)
        else:
            self.is_reference = False
        if hasattr(request, 'application'):
            self.url = URL(args=request.args)
            self.callback()
        else:
            self.url = request

    def callback(self):
        from gluon.serializers import json
        if 'request_json' in self.request.vars and self.request.vars.request_json == 'True':
            query = None
            if 'prefetch' in self.request.vars and self.request.vars.prefetch == 'True':
                self.limitby = None
                if not self.query:
                    query = self.fields[0]
                else:
                    query = self.query
            if 'remote' in self.request.vars:
                if not self.query:
                    query = self.fields[0].contains(self.request.vars.remote)
                else:
                    query = self.query & self.fields[0].contains(self.request.vars.remote)

            rows = self.db(query).select(
                orderby=self.orderby,
                limitby=self.limitby,
                distinct=self.distinct,
                *self.fields
            )

            if rows:
                raise HTTP(200, json(rows))
            else:
                raise HTTP(200, json([]))

    def __call__(self, field, value, **attributes):
        default = dict(
            _type='text',
            value=(value is not None and str(value)) or '',
        )
        attr = StringWidget._attributes(field, default, **attributes)

        attr['_name'] = field.name

        str_fields = ''
        for requested_field in self.fields:
            str_fields += requested_field.name + ': ' + 'item.' + requested_field.name + ','

        prefetch_code = """
                prefetch: {
                    url: '%(url)s?request_json=True&prefetch=True&lang='+encodeURIComponent('%(language)s'),
                    filter: function(list) {
                        return $.map(list, function(item) {
                            return {
                                %(fields)s
                            };
                        });
                    }
                },
        """ % dict(url=self.url, language=current.T.http_accept_language, fields=str_fields)



        remote_code = """
                remote: {
                    url: '%(url)s?request_json=True&remote=%%QUERY&lang='+encodeURIComponent('%(language)s'),
                    wildcard: '%%QUERY',
                    filter: function(list) {
                        return $.map(list, function(item) {
                            return {
                                %(fields)s
                            };
                        });
                    }
                },
        """ % dict(url=self.url, language=current.T.http_accept_language, fields=str_fields)

        bloodhound_code = """
            var items = new Bloodhound({
                datumTokenizer: Bloodhound.tokenizers.obj.whitespace('%(fieldname)s'),
                queryTokenizer: Bloodhound.tokenizers.whitespace,
                limit: 10,
                %(prefetch_code)s
                %(remote_code)s
            });
        """ % dict(fieldname=field.name,
                   prefetch_code=prefetch_code if self.prefetch else '',
                   remote_code=remote_code if self.remote else ''
                   )

        limit_by_code = 'limit: %s,' % self.limitby[1] if self.limitby else ''

        script = bloodhound_code + """
            $('#%(input_id)s').typeahead(
                {
                    hint: true,
                    highlight: true,
                    minLength: %(min_length)s
                },
                {
                    name: 'items',
                    displayKey: '%(fieldname)s',
                    source: items.ttAdapter(),
                    %(limit_by)s
                }
            );
        """ % dict(input_id=attr['_id'] if not self.is_reference else self.keyword,
                   min_length=self.min_length,
                   fieldname=self.fields[0].name,
                   limit_by=limit_by_code
                   )

        if self.is_reference:

            script += """
            $('#%(typeahead_id)s').bind('typeahead:select', function(ev, suggestion) {
                $('#%(input_id)s').val(suggestion.%(id_field_name)s);
            });
            """ % dict(
                input_id=attr['_id'],
                typeahead_id=self.keyword,
                id_field_name=self.id_field.name
            )

            del attr['_class']
            attr['_type'] = 'hidden'
            return CAT(
                INPUT(_id=self.keyword, _class='string form-control'),
                INPUT(**attr),
                SCRIPT(script)
            )
        else:
            attr['_class'] += ' form-control'
            return CAT(INPUT(**attr), SCRIPT(script))