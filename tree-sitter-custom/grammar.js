module.exports = grammar({
  name: 'custom',

  rules: {
    source_file: $ => repeat($._item),

    _item: $ => choice(
      $.text,
      $.yellow_highlight,
      $.green_highlight,
      $.red_highlight,
      $.blue_highlight,
      $.white_highlight,
      $.newline
    ),

    text: $ => /[^\n\[\]{}<>«»|]+/,
    
    yellow_highlight: $ => seq(
      '[',
      $.yellow_content,
      ']'
    ),
    
    green_highlight: $ => seq(
      '{',
      $.green_content,
      '}'
    ),
    
    red_highlight: $ => seq(
      '<',
      $.red_content,
      '>'
    ),
    
    blue_highlight: $ => seq(
      '«',
      $.blue_content,
      '»'
    ),
    
    white_highlight: $ => seq(
      '|',
      $.white_content,
      '|'
    ),
    
    yellow_content: $ => /[^\]]+/,
    green_content: $ => /[^}]+/,
    red_content: $ => /[^>]+/,
    blue_content: $ => /[^»]+/,
    white_content: $ => /[^|]+/,
    
    newline: $ => '\n'
  }
});