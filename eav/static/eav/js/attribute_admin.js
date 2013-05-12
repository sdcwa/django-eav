/*
 * Admin-only UI enhancements for eav Attribute model.
 */

// Wrap URLify to replace hyphens with underscores
var OldURLify = URLify;
var URLify = function(s, num_chars) { return OldURLify(s, num_chars).replace(/-/g, '_') };

// Hide data type select fields where necessary
(function($) {
    var data_type_fields = {
        'enum': 'enum_group',
        'tree': 'tree_item_parent'
    };

    function hideDataTypeFields(f) {
        for (type in data_type_fields) {
            $('.field-' + data_type_fields[type]).hide();
        }
        $('.field-' + data_type_fields[f.val()]).show();
    }

    $(document).ready(function() {
        dataTypeField = $('#id_datatype');
        hideDataTypeFields(dataTypeField);
        $('#id_datatype').change(function(e) {
            hideDataTypeFields(dataTypeField);
        });
    });
})(django.jQuery);
