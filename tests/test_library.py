def test_browse_root(library):
    results = library.browse('radionet:root')
    assert 7 == len(results)


def test_browse_localstations(library):
    results = library.browse('radionet:local')
    assert len(results) > 0

    page_uri = results[0].uri if results is not None else None
    assert page_uri is not None

    # 1 Page, not results
    # results = library.browse(page_uri)
    # assert len(results) > 0


def test_browse_genres(library):
    genres = library.browse('radionet:genres')
    assert len(genres) > 0

    cat_uri = genres[0].uri if genres is not None else None
    assert cat_uri is not None

    pages = library.browse(cat_uri)
    assert len(pages) == 7

    page_uri = pages[0].uri if pages is not None else None
    assert page_uri is not None

    results = library.browse(page_uri)
    assert len(results) > 0

    page_uri = pages[len(pages) - 1].uri if results is not None else None
    assert page_uri is not None

    results = library.browse(page_uri)
    assert len(results) > 0


def test_browse_topics(library):
    results = library.browse('radionet:topics')
    assert len(results) > 2

    cat_uri = results[2].uri if results is not None else None
    assert cat_uri is not None

    results = library.browse(cat_uri)
    assert len(results) > 2

    page_uri = results[0].uri if results is not None else None
    assert page_uri is not None

    # 1 Page, not results
    # results = library.browse(page_uri)
    # assert len(results) > 0


def test_browse_languages(library):
    results = library.browse('radionet:languages')
    assert len(results) > 0

    cat_uri = results[5].uri if results is not None else None
    assert cat_uri is not None

    results = library.browse(cat_uri)
    assert len(results) == 11

    page_uri = results[0].uri if results is not None else None
    assert page_uri is not None

    # 1 Page, not results
    # results = library.browse(page_uri)
    # assert len(results) > 0


def test_browse_cities(library):
    results = library.browse('radionet:cities')
    assert len(results) > 0

    cat_uri = results[0].uri if results is not None else None
    assert cat_uri is not None

    results = library.browse(cat_uri)
    assert len(results) == 2

    page_uri = results[0].uri if results is not None else None
    assert page_uri is not None

    # 1 Page, not results
    # results = library.browse(page_uri)
    # assert len(results) > 0


def test_browse_countries(library):
    results = library.browse('radionet:countries')
    assert len(results) > 0

    cat_uri = results[0].uri if results is not None else None
    assert cat_uri is not None

    results = library.browse(cat_uri)
    assert len(results) == 4

    page_uri = results[0].uri if results is not None else None
    assert page_uri is not None

    # 1 Page, not results
    # results = library.browse(page_uri)
    # assert len(results) > 0


def test_browse_favorites(library):
    results = library.browse('radionet:favorites')
    assert 1 == len(results)


def test_search(library):
    result = library.search({'any': ['katze']})

    assert len(result.tracks) > 0

    old_length = len(result.tracks)

    result = library.search({'any': ['katze']})

    assert len(result.tracks) == old_length


def test_lookup(library):
    results = library.browse('radionet:favorites')
    assert 1 == len(results)

    for result in results:
        assert library.lookup(result.uri) is not None


def test_track_by_slug(library):
    results = library.lookup('radionet:track:dancefm')
    assert 1 == len(results)
    assert results[0].uri == 'radionet:track:dancefm'
