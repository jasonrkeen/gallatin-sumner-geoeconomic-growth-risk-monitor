import copy
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import sample_run as sample
from src import composite_score as c
from src import scenario_forecast as s
from src import sensitivity_analysis as sensitivity
from src.config import classify_risk, RISK_SCORE_WEIGHTS


def test_hand_calculated_weighted_score_and_credit():
    # .20*10 + .15*(20+30+40+50) + .10*(60+70) = 36.
    inputs = {key: {"score": value} for key, value in zip(RISK_SCORE_WEIGHTS, range(10, 80, 10))}
    before = copy.deepcopy(inputs)
    score, detail = c.calculate_composite_risk(inputs)
    assert score == pytest.approx(36)
    assert detail.weighted_contribution.sum() == pytest.approx(36)
    assert c.calculate_resilience_credit(55) == 8.25
    assert c.calculate_adjusted_risk(score, 8.25) == pytest.approx(27.75)
    assert inputs == before


@pytest.mark.parametrize("offset,expected", [(-5,0),(0,0),(100,12.5),(np.nan,0)])
def test_credit_caps(offset, expected):
    assert c.calculate_resilience_credit(offset) == expected


@pytest.mark.parametrize("value,expected", [(0,"Low Risk"),(24.99,"Low Risk"),(25,"Moderate Risk"),
    (49.99,"Moderate Risk"),(50,"Elevated Risk"),(74.99,"Elevated Risk"),(75,"High Risk"),(100,"High Risk")])
def test_band_boundaries(value, expected):
    assert classify_risk(value) == expected


def test_missing_component_renormalization_and_empty_input():
    score, _ = c.calculate_composite_risk({"growth_pressure":{"score":20},
                                        "housing_affordability_pressure":{"score":80}})
    assert score == pytest.approx((.2*20+.15*80)/.35)
    assert np.isnan(c.calculate_composite_risk({})[0])
    assert c.calculate_adjusted_risk(5,12.5) == 0
    assert c.clamp_score(120) == 100


def test_hand_calculated_scenario_and_sensitivity():
    state = s.load_latest_model_state()
    state.update(composite_risk_score=40,adjusted_geoeconomic_growth_risk_score=34,
                 growth_pressure_score=20,construction_shock_score=60,
                 local_resilience_offset=40,resilience_credit_applied=6)
    before = copy.deepcopy(state)
    result = s.calculate_scenario_scores(state).set_index("scenario_key")
    # Managed growth: .3*40 + .25*20 + .25*60 + .2*55 - 6 = 37.
    assert result.loc["managed_growth","scenario_adjusted_risk_score"] == pytest.approx(37)
    assert result.loc["managed_growth","scenario_delta_vs_adjusted_baseline"] == pytest.approx(3)
    assert result.loc["overheated_growth","scenario_resilience_credit"] == 4.5
    assert result.scenario_adjusted_risk_score.between(0,100).all()
    assert state == before
    score, _ = sensitivity.calculate_weighted_score(pd.DataFrame([
        {"component":"a","score":20},{"component":"b","score":80}]), {"a":1,"b":3})
    assert score == 65
    with pytest.raises(ValueError):
        sensitivity.normalize_weights({"a":0})


def test_published_table_parity():
    tables = sample.calculate_sample()
    expected = pd.read_csv(sample.ROOT / "data/processed/composite_risk_score_latest.csv")
    actual = tables["composite_sample.csv"]
    pd.testing.assert_frame_equal(actual,expected[actual.columns],check_exact=False,rtol=0,atol=1e-10)
    for name in ["scenario_forecasts.csv", "sensitivity_analysis_results.csv"]:
        expected = pd.read_csv(sample.ROOT / "data/processed" / name)
        pd.testing.assert_frame_equal(tables[name],expected,check_exact=False,rtol=0,atol=1e-10)


def test_repeated_artifacts_and_receipts(tmp_path):
    first, second = sample.run_sample(tmp_path/"a"), sample.run_sample(tmp_path/"b")
    assert first == second
    for name, expected in first["artifact_sha256"].items():
        assert hashlib.sha256((tmp_path/"a"/name).read_bytes()).hexdigest() == expected
        assert (tmp_path/"a"/name).read_bytes() == (tmp_path/"b"/name).read_bytes()


def test_cli_independent_offline_processes(tmp_path):
    (tmp_path/"sitecustomize.py").write_text(
        "import socket\ndef blocked(*a, **k):\n raise RuntimeError('Network forbidden')\n"
        "socket.socket.connect=blocked\nsocket.socket.connect_ex=blocked\nsocket.create_connection=blocked\n")
    for name in ["a","b"]:
        result = subprocess.run([sys.executable,str(sample.ROOT/"sample_run.py"),"--output-dir",str(tmp_path/name)],
                                cwd=tmp_path,env=dict(os.environ,PYTHONPATH=str(tmp_path)),
                                text=True,capture_output=True,check=True)
        assert "sample complete" in result.stdout
    assert (tmp_path/"a/run_manifest.json").read_bytes() == (tmp_path/"b/run_manifest.json").read_bytes()


@pytest.mark.parametrize("path", [sample.ROOT,sample.ROOT.parent,sample.ROOT/"data/processed/new",sample.ROOT/"outputs/reports/new"])
def test_protected_destinations(path):
    with pytest.raises(ValueError):
        sample.destination_path(path)


def test_existing_output_untouched(tmp_path):
    (tmp_path/"sentinel").write_text("keep")
    with pytest.raises(FileExistsError):
        sample.run_sample(tmp_path)
    assert list(tmp_path.iterdir()) == [tmp_path/"sentinel"]
    assert (tmp_path/"sentinel").read_text() == "keep"


def test_missing_sample_inputs_fail_closed(monkeypatch,tmp_path):
    monkeypatch.setattr(sample,"ROOT",tmp_path)
    with pytest.raises(FileNotFoundError,match="Required stored input"):
        sample.calculate_sample()


def test_preserved_model_data_and_published_artifacts():
    record = json.loads((sample.ROOT/"tests/preserved_files.json").read_text())
    for name, expected in record["files"].items():
        content = (sample.ROOT/name).read_bytes()
        if expected["text_lf"]:
            content = content.replace(b"\r\n",b"\n")
        assert hashlib.sha256(content).hexdigest() == expected["sha256"], name
