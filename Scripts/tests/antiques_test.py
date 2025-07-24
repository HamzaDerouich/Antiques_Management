# Pruebas unitarias para el scraper de antigüedades
import unittest
from unittest.mock import MagicMock
from scraping.antiques_scraper import AntiquesScraper

class TestAntiquesScraper(unittest.TestCase):
    def setUp(self):
        self.driver = MagicMock()
        self.wait = MagicMock()
        self.config = MagicMock()
        self.backup_manager = MagicMock()
        self.scraper = AntiquesScraper(self.driver, self.wait, self.config, self.backup_manager)

    def test_summarize_description_basic(self):
        html = "<div>Height: 50cm Width: 30cm Mahogany made in Ireland. Inlaid decoration. Original condition.</div>"
        summary = self.scraper.summarize_description(html)
        self.assertIn("Height: 50", summary)
        self.assertIn("Width: 30", summary)
        self.assertIn("Materials: Mahogany", summary)
        self.assertIn("Provenance: Ireland", summary)
        self.assertIn("Features: Inlaid decoration, Original condition", summary)
        self.assertIn("State: Original condition", summary)

    def test_get_item_images_from_td_empty(self):
        td = MagicMock()
        td.find_element.side_effect = Exception("No link")
        images = self.scraper.get_item_images_from_td(td)
        self.assertEqual(images, [])

    def test_scrape_page_calls_config(self):
        self.scraper.config.navigate_to_page = MagicMock()
        self.scraper.wait.until = MagicMock()
        self.scraper.driver.find_elements = MagicMock(return_value=[])
        self.scraper.scrape_page(1)
        self.scraper.config.navigate_to_page.assert_called_with(1)

if __name__ == "__main__":
    unittest.main()
