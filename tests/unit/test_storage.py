import mia.archiver.storage as storage

def test_basic_path_management():
    store = storage.Storage(
        "./test_snapshots",
        "web"
    )

    assert store.get_target_path(
        "https://codeberg.org/LunarWatcher/MIArchive"
    ) == store.target_directory + "/https:__codeberg.org_LunarWatcher_MIArchive"

def test_get_parameter_resolution():
    store = storage.Storage(
        "./test_snapshots",
        "web"
    )

    for _ in range(0, 10):
        assert store.get_target_path("https://example.com?abcd=1234") \
            == store.target_directory + "/https:__example.com@0"

        assert "https://example.com" in store.base_urls
        assert len(store.base_urls) == 1
        assert len(store.base_urls["https://example.com"]) == 1


    for _ in range(0, 10):
        assert store.get_target_path("https://example.com?abcd=12345") \
            == store.target_directory + "/https:__example.com@1"

        assert len(store.base_urls) == 1
        assert len(store.base_urls["https://example.com"]) == 2

def test_forced_truncation():
    store = storage.Storage(
        "./test_snapshots",
        "web"
    )

    url = store.get_target_path("https://abcd" + ("a" * 500))
    print(store.target_directory)
    assert len(url) == (250
        # Compensate for the length of the target directory
        + len(store.target_directory)
        # Compensate for the / added between the sanitised URL and the
        # directory
        + 1
    )



