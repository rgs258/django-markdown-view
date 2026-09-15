# Test App README

Welcome to the `testapp` fixture used by `markdown_view`'s test suite.

## Section One

This is the first section. It has a [link to another routed page](docs/OTHER.md)
and a [link to a specific section of that page](docs/OTHER.md#section-two).

## Section Two

This section links to a [page that isn't routed anywhere](UNROUTED.md), so
that link should be left exactly as markdown rendered it.

It also links to an [absolute path](/somewhere/), a
[fully-qualified URL](https://example.com), and a
[mailto link](mailto:someone@example.com), none of which should be touched.

It links to a [non-markdown file](notes.txt) and includes an inline image:

![An inline image](image.png)

Here is a fenced code block:

```python
def hello():
    return "world"
```

And here is a table:

| Column A | Column B |
| -------- | -------- |
| 1        | 2        |
| 3        | 4        |
