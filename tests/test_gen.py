from pathlib import Path

import pytest

from johnnydep.lib import JohnnyDist
from johnnydep.lib import JohnnyError


here = Path(__file__).parent


def test_generated_metadata_from_dist_name(make_dist):
    make_dist()
    jdist = JohnnyDist("jdtest")
    expected_metadata = {
        "author": "default author",
        "author_email": "default@example.org",
        "description": "default long text for PyPI landing page \U0001f4a9",
        "home_page": "https://www.example.org/default",
        "license": "MIT",
        "metadata_version": "2.1",
        "name": "jdtest",
        "platform": ["default platform"],
        "summary": "default text for metadata summary",
        "version": "0.1.2",
    }
    # different versions of setuptools can put a different number of newlines at the
    # end of the long description metadata
    assert jdist.metadata.pop("description").rstrip() == expected_metadata.pop("description")
    assert jdist.metadata == expected_metadata


def test_generated_metadata_from_dist_path(make_dist):
    dist_path = make_dist()
    jdist = JohnnyDist(dist_path)
    expected_metadata = {
        "author": "default author",
        "author_email": "default@example.org",
        "description": "default long text for PyPI landing page \U0001f4a9",
        "home_page": "https://www.example.org/default",
        "license": "MIT",
        "metadata_version": "2.1",
        "name": "jdtest",
        "platform": ["default platform"],
        "summary": "default text for metadata summary",
        "version": "0.1.2",
    }
    assert jdist.metadata.pop("description").rstrip() == expected_metadata.pop("description")
    assert jdist.metadata == expected_metadata


def test_build_from_sdist(add_to_index):
    add_to_index(here / "copyingmock-0.2.tar.gz")
    dist = JohnnyDist("copyingmock")
    assert dist.name == "copyingmock"
    assert dist.summary == "A subclass of MagicMock that copies the arguments"
    assert dist.required_by == []
    assert dist.import_names == ["copyingmock"]
    assert dist.homepage == "https://github.com/wimglenn/copyingmock"
    assert dist.extras_available == []
    assert dist.extras_requested == []
    assert dist.project_name == "copyingmock"
    assert dist.download_link.startswith("file://")
    assert dist.download_link.endswith("copyingmock-0.2.tar.gz")
    assert dist.checksum[:71] == "sha256=fa4c8aad336f6e74f7632f40ff5a271130be5def44ab3177af4578c4d4a66093"


def test_plaintext_whl_metadata(add_to_index):
    # this dist uses an old-skool metadata version 1.2
    add_to_index(here / "testpath-0.3.1-py2.py3-none-any.whl")
    dist = JohnnyDist("testpath==0.3.1")
    assert dist.serialise(fields=["name", "summary", "import_names", "homepage"]) == [
        {
            "name": "testpath",
            "summary": "Test utilities for code working with files and commands",
            "import_names": ["testpath"],
            "homepage": "https://github.com/jupyter/testpath",
        }
    ]


def test_old_metadata_20(add_to_index):
    # the never-officially-supported-but-out-in-the-wild metadata 2.0 spec (generated by wheel v0.30.0)
    add_to_index(here / "m20dist-0.1.2-py2.py3-none-any.whl")
    jdist = JohnnyDist("m20dist")
    expected_metadata = {
        "author": "default author",
        "author_email": "default@example.org",
        "description": "default long text for PyPI landing page \U0001f4a9\n\n\n",
        "home_page": "https://www.example.org/default",
        "license": "MIT",
        "metadata_version": "2.0",
        "name": "m20dist",
        "platform": ["default platform"],
        "summary": "default text for metadata summary",
        "version": "0.1.2",
    }
    assert jdist.metadata == expected_metadata
    assert jdist.checksum == "sha256=bdcb144db3ba4beebbf5f8b249302560e8894bce6c3688dc79f587d6272ecea4,sha1=7c64e8387cfae12e256f8e906755805ef21e7452,md5=488652bac3e1705e5646ea6a51f4d441"


def test_cant_pin(make_dist, mocker):
    make_dist(name="cantpin", version="0.6")
    jdist = JohnnyDist("cantpin")
    mocker.patch.object(jdist, "versions_available", [])
    with pytest.raises(JohnnyError) as cm:
        jdist.pinned
    assert str(cm.value) == "Can not pin because no version available is in spec"


def test_whl_extras():
    whl_path = here / "testwhlextra-1.0.0-py3-none-any.whl"
    jdist = JohnnyDist(f"{whl_path}[dev]")
    assert jdist.extras_requested == ["dev"], "should have found the extra dev deps"
    assert jdist.requires == ["black==22.1.0", "flake8==4.0.1", "xdoctest>=1.0.0"]
    assert JohnnyDist(whl_path).requires == ["xdoctest>=1.0.0"]
