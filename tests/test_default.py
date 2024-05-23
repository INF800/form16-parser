import json
import pytest

from form16_parser import (
    build_parser,
    UnsupportedForm16Error,
)


@pytest.mark.parametrize(
    ("uid", "filepath", "password", "parsed"),
    values := [
        ( 
            "0001_fy2324_parta_partb", 
            "tests/data/0001_fy2324_parta_partb.pdf",
            None,
            "tests/data/0001_fy2324_parta_partb.json",
        ),
        (
            "0002_fy2324_parta", 
            "tests/data/0002_fy2324_parta.pdf",
            None,
            "tests/data/0002_fy2324_parta.json",
        ),
        (
            # Raise "unsupported" exception
            "0003_fy1920_parta_partb", 
            "tests/data/0003_fy1920_parta_partb.pdf",
            None,
            "tests/data/0003_fy1920_parta_partb.json",
        ),
        (
            "0004_fy_2021_parta_partb", 
            "tests/data/0004_fy_2021_parta_partb.pdf",
            None,
            "tests/data/0004_fy_2021_parta_partb.json",
        ),
        (
            "0005_fy2122_parta_partb", 
            "tests/data/0005_fy2122_parta_partb.pdf",
            None,
            "tests/data/0005_fy2122_parta_partb.json",
        ),
        (
            "0006_fy2324_parta_partb", 
            "tests/data/0006_fy2324_parta_partb.pdf",
            None,
            "tests/data/0006_fy2324_parta_partb.json",
        ),
        (
            "0007_fy2223_partb", 
            "tests/data/0007_fy2223_partb.pdf",
            None,
            "tests/data/0007_fy2223_partb.json",
        ),
        (
            "0008_fy2324_partb", 
            "tests/data/0008_fy2324_partb.pdf",
            None,
            "tests/data/0008_fy2324_partb.json",
        ),
        (
            "0010_fy2324_partb", 
            "tests/data/0010_fy2324_partb.pdf",
            None,
            "tests/data/0010_fy2324_partb.json",
        ),
        (
            "0011_fy2324_parta_partb_centralgov", 
            "tests/data/0011_fy2324_parta_partb_centralgov.pdf",
            None,
            "tests/data/0011_fy2324_parta_partb_centralgov.json",
        ),
        (
            "0012_fy2324_parta_partb_beg_q2", 
            "tests/data/0012_fy2324_parta_partb_beg_q2.pdf",
            None,
            "tests/data/0012.json",
        ),
        (
            "0013_fy2324_partb", 
            "tests/data/0013_fy2324_partb.pdf",
            None,
            "tests/data/0013.json",
        ),
        (
            "0014_fy2324_part_a_part_b", 
            "tests/data/0014_fy2324_part_a_part_b.pdf",
            None,
            "tests/data/0014.json",
        ),
        (
            "0015_fy2324_partb_trunc_verification", 
            "tests/data/0015_fy2324_partb_trunc_verification.pdf",
            None,
            "tests/data/0015.json",
        ),
        (
            "0016_fy2324_partb", 
            "tests/data/0016_fy2324_partb.pdf",
            None,
            "tests/data/0016.json",
        ),
        (
            "0017_fy2324_parta_partb", 
            "tests/data/0017_fy2324_parta_partb.pdf",
            None,
            "tests/data/0017.json",
        ),
        (
            "0018_fy2324_parta", 
            "tests/data/0018_fy2324_parta.pdf",
            None,
            "tests/data/0018.json",
        ),
        (
            "0020_fy2324_partb_honeywell", 
            "tests/data/0020_fy2324_partb_honeywell.pdf",
            None,
            "tests/data/0020.json",
        ),
        (
            # Raise "unsupported" exception
            "0021_fy2021_parta_partb", 
            "tests/data/0021_fy2021_parta_partb.pdf",
            None,
            "tests/data/0021.json",
        ),
        (
            "0021_fy2324_parta_partb_bbeforea", 
            "tests/data/0021_fy2324_parta_partb_bbeforea.pdf",
            None,
            "tests/data/0021.json",
        ),
        (
            "0022_fy1617_parta_invalidb", 
            "tests/data/0022_fy1617_parta_invalidb.pdf",
            None,
            "tests/data/0022.json",
        ),

    ],
    ids = [v[0] for v in values],
)
def test_parser(uid, filepath, password, parsed):
    if ("fy1920" in filepath) or ("fy2021" in filepath):  # Check if the test case corresponds to FY 2019-20
        with pytest.raises(UnsupportedForm16Error) as exc_info:
            build_parser().parse(filepath, return_output=True)
        assert str(exc_info.value) == "At this point in time, we do not support form 16s older than FY2122. But stay tuned, future releases will definitely work for them! You can remove this execption manually and parse them anyway."
    else:
        with open(parsed, "r") as fp:
            expected_data = json.load(fp)
        p = build_parser()
        data = p.parse(filepath, return_output=True)
        assert data == expected_data