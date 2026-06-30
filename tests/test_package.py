def test_package_exposes_version():
    import ecg_viewer

    assert ecg_viewer.__version__ == "0.1.0"
