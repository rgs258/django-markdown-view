# Escaping Test

This paragraph documents a block tag that was never meant to run:
`{% include 'whatever.html' %}` should render as literal text.

This paragraph documents a variable that was never meant to resolve:
`{{ some_undocumented_variable }}` should also render as literal text.

Here's an image, whose injected `{% static %}` tag must still resolve
normally:

![An inline image](image.png)

pk is "{{ pk }}".
