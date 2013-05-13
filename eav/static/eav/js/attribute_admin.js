/*
 * Admin-only UI enhancements for eav Attribute model.
 */

// Wrap URLify to replace hyphens with underscores
var OldURLify = URLify;
var URLify = function(s, num_chars) { return OldURLify(s, num_chars).replace(/-/g, '_') };
