# tests/test_generator.py

from src.generator import generate


def test_story_generation():

    req = """
    User should login using email and password
    """

    result = generate(req)

    assert result is not None


def test_ecommerce_generation():

    req = """
    Customer can search products,
    add to cart and checkout
    """

    result = generate(req)

    assert result is not None


def test_agriculture_generation():

    req = """
    Monitor soil moisture,
    crop health and weather.
    """

    result = generate(req)

    assert result is not None