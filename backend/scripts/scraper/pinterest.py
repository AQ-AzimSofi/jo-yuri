"""
Pinterest Image Scraper

Scrapes images from Pinterest boards/search results using Playwright.
"""

import asyncio
import hashlib
import httpx
from pathlib import Path
from playwright.async_api import async_playwright
from typing import Optional


class PinterestScraper:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def scrape_board(
        self,
        board_url: str,
        max_images: int = 50,
        scroll_delay: float = 1.5,
    ) -> list[Path]:
        """
        Scrape images from a Pinterest board.

        Args:
            board_url: URL of the Pinterest board
            max_images: Maximum number of images to download
            scroll_delay: Delay between scrolls in seconds

        Returns:
            List of paths to downloaded images
        """
        downloaded = []
        seen_urls = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.set_default_timeout(60000)  # 60s timeout

            await page.goto(board_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)  # Wait for images to load

            while len(downloaded) < max_images:
                # Extract image URLs
                images = await page.query_selector_all('img[src*="pinimg.com"]')

                for img in images:
                    if len(downloaded) >= max_images:
                        break

                    src = await img.get_attribute("src")
                    if not src or src in seen_urls:
                        continue

                    # Get highest resolution version
                    high_res_url = self._get_high_res_url(src)
                    seen_urls.add(src)

                    # Download image
                    path = await self._download_image(high_res_url)
                    if path:
                        downloaded.append(path)
                        print(f"Downloaded {len(downloaded)}/{max_images}: {path.name}")

                # Scroll down to load more
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(scroll_delay)

                # Check if we've reached the end
                new_height = await page.evaluate("document.body.scrollHeight")
                if len(images) == 0:
                    break

            await browser.close()

        return downloaded

    async def scrape_search(
        self,
        query: str,
        max_images: int = 50,
    ) -> list[Path]:
        """
        Scrape images from Pinterest search results.

        Args:
            query: Search query (e.g., "jo yuri izone")
            max_images: Maximum number of images to download

        Returns:
            List of paths to downloaded images
        """
        search_url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
        return await self.scrape_board(search_url, max_images)

    def _get_high_res_url(self, url: str) -> str:
        """Convert thumbnail URL to high-res version."""
        # Pinterest URL patterns: /236x/, /474x/, /736x/, /originals/
        for size in ["/236x/", "/474x/", "/736x/"]:
            if size in url:
                return url.replace(size, "/originals/")
        return url

    def _get_fallback_url(self, url: str) -> str:
        """Get a medium-res fallback if originals fail."""
        if "/originals/" in url:
            return url.replace("/originals/", "/736x/")
        return url

    async def _download_image(
        self, url: str, original_url: str | None = None, min_size: int = 10_000
    ) -> Optional[Path]:
        """Download an image and return its path. Falls back to lower res on 403."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=30)
                response.raise_for_status()

                content = response.content

                # Skip tiny images (likely broken/placeholders)
                if len(content) < min_size:
                    print(f"Skipping {url}: too small ({len(content)} bytes)")
                    return None

                # Generate filename from URL hash
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                ext = self._get_extension(response.headers.get("content-type", ""))
                filename = f"{url_hash}{ext}"
                filepath = self.output_dir / filename

                filepath.write_bytes(content)
                return filepath

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403 and "/originals/" in url:
                # Fallback to 736x resolution
                fallback = self._get_fallback_url(url)
                return await self._download_image(fallback, original_url=url)
            print(f"Failed to download {url}: {e}")
            return None
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return None

    def _get_extension(self, content_type: str) -> str:
        """Get file extension from content type."""
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        return mapping.get(content_type, ".jpg")


async def main():
    """CLI usage example."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape images from Pinterest")
    parser.add_argument("url", help="Pinterest board URL or search query")
    parser.add_argument("--max", type=int, default=50, help="Max images to download")
    parser.add_argument("--output", type=str, default="data/images", help="Output dir")
    parser.add_argument("--search", action="store_true", help="Treat input as search query")
    args = parser.parse_args()

    scraper = PinterestScraper(Path(args.output))

    if args.search:
        downloaded = await scraper.scrape_search(args.url, args.max)
    else:
        downloaded = await scraper.scrape_board(args.url, args.max)

    print(f"\nDownloaded {len(downloaded)} images to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
