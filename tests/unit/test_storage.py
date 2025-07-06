import mia.archiver.storage as storage

def test_basic_path_management():
    store = storage.Storage(
        "./test_snapshots",
        "web"
    )

    assert store.get_target_path(
        "https://codeberg.org/LunarWatcher/MIArchive"
    ) == store.target_directory + "/https:__codeberg.org_LunarWatcher_MIArchive"
