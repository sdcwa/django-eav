/*
 * A jQuery plugin to allow TreeItem fields to discover their children
 */

$.fn.populateSelect = function(data, url) {
  this_id = '#' + this.attr('id');
  $.getJSON(url, data, function(json) {
    $('option', this_id).remove();
    $.each(json, function() {
      var option = $('<option />').val(this[0]).text(this[1]);
      $(this_id).append(option);
    });
  });
};

$.fn.treefield = function(childUrl) {
  var id_regex = /(\d+)$/;

  this_id = this.attr('id');
  id = parseInt(id_regex.exec(this_id)[0]);
  child_id = this_id.replace(id_regex, id + 1)

  $child = $('#' + child_id);

  if (!$child.length>0) {
    return this;
  }

  this.change(function(e) {
    $child.populateSelect({'parent': $(this).val()}, childUrl)
  });
};
