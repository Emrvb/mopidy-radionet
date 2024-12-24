

def test_get_genres(radionet):
    genres = radionet.get_genres()
    assert len(genres) > 0

def test_get_local_stations(radionet):
    result = radionet.get_simple_category('local', 1)
    assert len(result) > 0


def test_do_search(radionet):
    result = radionet.do_search("\"radio ram\"")
    assert len(result) > 0

    assert result[0].stream_url is not None

    assert radionet.get_stream_url(result[0].id) is not None


def test_get_favorites(radionet):
    radionet.cache = {}
    test_favorites = ["rockantenne", "eska", "dancefm"]
    radionet.set_favorites(test_favorites)
    result = radionet.get_favorites()
    assert len(result) == len(test_favorites)

    assert result[1].name == 'Eska'


def test_favorites_broken_slug(radionet):
    radionet.cache = {}
    test_favorites = ["radio 357"]
    radionet.set_favorites(test_favorites)
    result = radionet.get_favorites()
    assert len(result) == 1
