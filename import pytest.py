import pytest
from Antiques import summarize_description

# test_Antiques.py


def test_full_fields():
    html = """
    <div>
        <p>Height: 120cm, Width: 50cm, Depth: 30cm</p>
        <p>Material: Mahogany, Bronze, Glass</p>
        <p>Made in France</p>
        <p>This rare piece is in original condition with inlaid decoration and provenance available.</p>
    </div>
    """
    summary = summarize_description(html)
    assert "Height: 120" in summary
    assert "Width: 50" in summary
    assert "Depth: 30" in summary
    assert "Materials: Bronze, Glass, Mahogany" in summary
    assert "Provenance: Made in France" in summary
    assert "Features: Inlaid decoration, Original condition, Provenance available, Rare piece" in summary
    assert "State: Original condition" in summary

def test_partial_fields():
    html = """
    <div>
        <p>Height: 80cm</p>
        <p>Material: Oak</p>
        <p>Restored and cleaned recently.</p>
    </div>
    """
    summary = summarize_description(html)
    assert "Height: 80" in summary
    assert "Materials: Oak" in summary
    assert "State: Restored/Cleaned" in summary

def test_no_fields():
    html = "<div><p>This is a simple antique item with no special info.</p></div>"
    summary = summarize_description(html)
    assert summary.startswith("This is a simple antique item")
    assert len(summary) <= 200

def test_empty_html():
    html = ""
    summary = summarize_description(html)
    assert summary == ""

def test_html_with_tags_and_whitespace():
    html = """
    <div>
        <p>
            Height: 100 cm
            <br>
            Material:    Silver
        </p>
        <p>
            Provenance: Located in Ireland
        </p>
    </div>
    """
    summary = summarize_description(html)
    assert "Height: 100" in summary
    assert "Materials: Silver" in summary
    assert "Provenance: Provenance: Located in Ireland" in summary

def test_multiple_materials_and_features():
    html = """
    <div>
        <p>Height: 45cm</p>
        <p>Material: Gold, Ivory, Ebony, Oak</p>
        <p>This rare piece features crossed ferns and is inlaid. Original condition.</p>
    </div>
    """
    summary = summarize_description(html)
    # Materials should be sorted and unique
    assert "Materials: Ebony, Gold, Ivory, Oak" in summary
    assert "Features: Inlaid decoration, Crossed Ferns motif, Original condition, Rare piece" in summary

def test_provenance_ireland():
    html = "<div><p>This item originates from Ireland and is made of walnut.</p></div>"
    summary = summarize_description(html)
    assert "Provenance: Ireland" in summary
    assert "Materials: Walnut" in summary