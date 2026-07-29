from responder import compress_docs


def test_compress_docs_removes_duplicates_and_truncates():
    docs = [
        "  Refund policy for duplicate charges.  ",
        "Refund policy for duplicate charges.",
        "",
        "Please contact support if the refund is delayed for more than 3 business days.",
        "Please contact support if the refund is delayed for more than 3 business days.",
    ]

    compressed = compress_docs(docs, max_docs=2, max_chars=120)

    assert compressed == [
        "Refund policy for duplicate charges.",
        "Please contact support if the refund is delayed for more than 3 business days.",
    ]
